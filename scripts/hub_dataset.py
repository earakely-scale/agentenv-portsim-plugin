"""Build the Hugging Face dataset earakely-scale/PortSimEnv-AgentEnv from this checkout and the recorded sweeps, and
push it. Two kinds of tables share the repo:

- PortSim's, one family per version (v4 wind, v3 marine, v2 live, v1): the weeks with what the agent is told and the
  reference costs, the recorded runs with their grades and chat transcripts, and the references.
- agentenv-hf's, one per bundle, as `agent-env hf publish` writes them: the bundle's tasks and runs, each run's record
  and native trajectory, and the bundle itself, which `agent-env hf run` runs. A version's runs come from several
  sweeps, each played from a bundle of its own, so they are built sweep by sweep and joined under the version's
  bundle name.

The card is hub/dataset/README.md, with each bundle's configs and needs added by agentenv-hf's card writer. The runs
are read from results/runs and from the agent-env stores the sweeps wrote them to. Every file goes through
agentenv-hf's check for keys and token shapes before anything is written, and --repo pushes the folder as one commit
on top of the commit it read, removing what the build no longer writes.

    uv run python scripts/hub_dataset.py --out build/hub/dataset
    uv run python scripts/hub_dataset.py --out build/hub/dataset --repo earakely-scale/PortSimEnv-AgentEnv --tag v0.4.0
"""

import argparse
import io
import json
import shutil
import tomllib
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from agent_env.store.routing import namespace_routing
from agentenv_hf import dataset, records, runs, tables
from agentenv_hf.card import card
from agentenv_hf.messages import to_messages
from agentenv_hf.scan import known_values, scan
from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi

from agentenv_portsim import marine, tasks, wind
from agentenv_portsim.schedule import MARINE_ENV, WIND_ENV, WIND_MAX_TURNS, schedule
from agentenv_portsim.sweep import EVAL_PACK, RUNS, results

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "hub/dataset/README.md"
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
WEATHER = ROOT / "data/wind/weather.jsonl"
SPLIT = "eval"
SWEEPS = ["wind-pilot-gpt", "wind-gpt", "wind-pilot-sonnet", "wind-sonnet", "marine-pilot-gpt", "marine-gpt",
          "marine-pilot-sonnet", "marine-sonnet", "live-pilot-gpt", "live-gpt", "live-pilot-sonnet", "live-sonnet",
          "g2"]
BUNDLES = {"v4": f"{EVAL_PACK}-wind", "v3": f"{EVAL_PACK}-marine", "v2": f"{EVAL_PACK}-live", "v1": EVAL_PACK}
REFERENCE_FILES = {"v4": ("wind", wind.REFERENCES), "v3": ("marine", marine.REFERENCES),
                   "v2": ("live", tasks.REFERENCES)}
SETUP = "agent-env portsim setup --agent"
NAMES = {"openai/gpt-6.1-sol": "GPT-6.1 Sol", "anthropic/claude-sonnet-5-5": "Claude Sonnet 5.5"}
MESSAGES = pa.field("messages", pa.list_(tables.MESSAGE))


def version_of(sweep: dict) -> str:
    return "v4" if sweep.get("wind") else "v3" if sweep.get("marine") else "v2" if sweep.get("live") else "v1"


def play_step(task, version: str) -> dict:
    task_steps = {"v1": lambda: tasks.steps(task, 5.0), "v2": lambda: tasks.live_steps(task, 5.0),
                  "v3": lambda: tasks.live_steps(task, 5.0, env=MARINE_ENV, week=marine.MarineWeek),
                  "v4": lambda: tasks.live_steps(task, 5.0, env=WIND_ENV, week=wind.WindWeek, rules=tasks.WIND_RULES,
                                                 max_turns=WIND_MAX_TURNS)}[version]()
    return next(s for s in task_steps if s["id"] == "play")


def wind_windows(weather: dict) -> str:
    return json.dumps([{"start": w["start"], "end": w["end"], "above_kn": 25 if w["min_length"] else 30,
                        "unvalidated": w["unvalidated"]} for w in weather["windows"]])


def task_row(task, version: str, reference: dict | None, raw: str, weathers: dict) -> dict:
    play = play_step(task, version)
    row = {"task_id": task.task_id, "quay": task.quay, "terminal": task.terminal, "difficulty": task.difficulty,
           "week": task.week, "week_start_utc": task.week_start_utc, "num_ships": len(task.ships),
           "num_disruptions": len(task.disruptions), "system_prompt": play["system_prompt"],
           "situation": play["prompt"], "optimal_cost": task.reference["optimal_cost"]}
    if version == "v1":
        return row | {"naive_cost": task.reference["naive_cost"], "proven_optimal": task.reference["proven_optimal"],
                      "optimal_plan": json.dumps(task.reference["optimal_plan"]),
                      "naive_plan": json.dumps(task.reference["naive_plan"]), "task": raw}
    watches = schedule(task)
    row |= {"num_watches": len(watches), "unavoidable_cost": reference["unavoidable_cost"],
            "rolling_cost": reference["rolling"]["cost"], "naive_cost": reference["naive"]["cost"],
            "naive_feasible": reference["naive"]["feasible"]}
    if version in ("v3", "v4"):
        pools = task.rules["marine"]
        row |= {"pilots": pools["pilots"], "tugs": pools["tugs"], "other_movements": len(pools["movements"])}
    if version == "v3":
        row["v2_optimal_cost"] = reference["v2_optimal_cost"]
    if version == "v4":
        weather = weathers[reference["weather"]]
        row |= {"schedule": reference["schedule"], "v3_optimal_cost": reference["v3_optimal_cost"],
                "hindsight_cost": reference["hindsight_cost"], "blind_cost": reference["blind"]["cost"],
                "blind_feasible": reference["blind"]["feasible"], "weather_id": weather["id"],
                "weather_week": weather["iso_week"], "weather_monday_utc": weather["monday"],
                "weather_kind": weather["kind"], "wind_windows": wind_windows(weather)}
    return row | {"watches": json.dumps([{"watch": w.index, "hour": w.hour,
                                          "notices": [{"from": n.name, "about_hour": n.event_hour, "text": n.text}
                                                      for n in w.notices]} for w in watches], ensure_ascii=False),
                  "task": raw}


def episode_rows(sweep_dir: Path, version: str, by_id: dict, episode_ids: dict[str, str]) -> list[dict]:
    rows = []
    for r in results(sweep_dir):
        if r["outcome"] != "scored":
            continue
        record = json.loads((sweep_dir / r["transcript"]).read_text())
        task = by_id[r["task_id"]]
        row = {"episode_id": episode_ids[r["instance"]], "model": r["model"],
               "model_name": NAMES.get(r["model"], r["model"]), "task_id": r["task_id"],
               "difficulty": task.difficulty, "quay": task.quay, "num_ships": len(task.ships), "reward": r["reward"],
               "feasible": r["feasible"], "cost": r["plan_cost"], "optimal_cost": r["optimal_cost"],
               "turns": r["turns"], "tool_calls": r["tool_calls"], "input_tokens": r["input_tokens"],
               "output_tokens": r["output_tokens"], "cost_usd": r["cost_usd"], "end_reason": r["end_reason"],
               "sweep": sweep_dir.name}
        if version == "v1":
            row |= {"submitted": r["submitted"], "checks": r["checks"]}
        else:
            row |= {"num_watches": r["watches"], "regret": r["regret"], "excused_cost": r["excused_cost"]}
        rows.append(row | {"final_plan": json.dumps(record["final"].get("plan")),
                           "steps": json.dumps(record["steps"], ensure_ascii=False),
                           "messages": to_messages(record)})
    return rows


def reference_row(r: dict) -> dict:
    flat = {"task_id": r["task_id"], "qualifies": r["qualifies"], "optimal_cost": r["optimal_cost"],
            "unavoidable_cost": r["unavoidable_cost"], "watch_hours": r["watch_hours"]}
    for key in ("v2_optimal_cost", "schedule", "weather", "kind", "hindsight_cost", "v3_optimal_cost",
                "added_watches"):
        if key in r:
            flat[key] = r[key]
    for policy in ("rolling", "blind", "hold", "naive"):
        if policy in r:
            flat |= {f"{policy}_{k}": r[policy][k] for k in ("cost", "reward", "feasible", "excused_cost")}
    if "clauses" in r:
        flat["clauses"] = json.dumps(r["clauses"])
    return flat | {"rolling_plans": json.dumps(r["rolling"]["plans"]), "configs": json.dumps(r["configs"]),
                   "solver": json.dumps(r["solver"])}


def table_bytes(rows: list[dict]) -> bytes:
    """The rows as parquet, with ``messages``, when there, typed as agentenv-hf types its chat transcripts."""
    keys = dict.fromkeys(k for row in rows for k in row if k != "messages")
    schema = pa.Table.from_pylist([{k: row.get(k) for k in keys} for row in rows]).schema
    if rows and "messages" in rows[0]:
        schema = schema.append(MESSAGES)
    return tables.parquet(rows, schema)


def raw_lines(pack_dir: Path) -> dict[str, str]:
    return {json.loads(line)["task_id"]: line for line in (pack_dir / "tasks.jsonl").read_text().splitlines()}


def agentenv_files(name: str, bundle: Path, sweeps: list[tuple[Path, list[str]]]) -> tuple[dict[str, bytes], dict]:
    """agentenv-hf's files for the bundle ``name``: its tasks from ``bundle``, and the runs ``sweeps`` list by instance
    id, each sweep built from its own bundle under ``name``. Returns the files and each instance's episode id."""
    files = dataset.build(runs.locate(str(bundle)), name=name, split=SPLIT, which="latest").files
    parts, raw, episode_ids = [], {}, {}
    for sweep_dir, ids in sweeps:
        played = runs.locate(str(sweep_dir / "bundle"))
        built = dataset.build(played, name=name, split=SPLIT, which="latest", instance_ids=tuple(ids)).files
        parts.append(pq.read_table(io.BytesIO(built[f"episodes/{name}.parquet"])))
        for line in built[f"raw/{name}.jsonl"].decode().splitlines():
            raw[json.loads(line)["episode_id"]] = line
        rewrite = records.Rewrite(played.id_root, name)
        episode_ids |= {i: rewrite.text(i) for i in ids}
    episodes = pa.concat_tables(parts).sort_by([("model", "ascending"), ("task", "ascending")])
    sink = io.BytesIO()
    pq.write_table(episodes, sink)
    files[f"episodes/{name}.parquet"] = sink.getvalue()
    files[f"raw/{name}.jsonl"] = "".join(raw[i] + "\n" for i in episodes.column("episode_id").to_pylist()).encode()
    return files, episode_ids


def card_text(plugin: str) -> str:
    """hub/dataset/README.md with each bundle's two configs and its needs, as agentenv-hf's publish writes them."""
    text = CARD.read_text()
    for name in BUNDLES.values():
        text = card(text, name=name, split=SPLIT, repo=None, description=None, license=None,
                    needs={"plugins": [plugin], "setup": SETUP})
    return text


def build(sweeps: list[str], runs_dir: Path, out: Path, plugin: str) -> dict[str, bytes]:
    pack = tasks.pack_tasks(EVAL_PACK)
    by_version = {"v1": {t.task_id: t for t in pack}, "v2": {t.task_id: t for t in pack},
                  "v3": {t.task_id: t for t in marine.pack().tasks}, "v4": {t.task_id: t for t in wind.pack().tasks}}
    raw = {"v1": raw_lines(tasks.PACKS / EVAL_PACK), "v2": raw_lines(tasks.PACKS / EVAL_PACK),
           "v3": raw_lines(marine.pack_dir()), "v4": raw_lines(wind.pack_dir())}
    refs = {"v2": tasks.live_references(), "v3": marine.references(), "v4": wind.references()}
    ids = {"v1": [t.task_id for t in pack], "v2": tasks.live_task_ids(), "v3": marine.task_ids(),
           "v4": wind.task_ids()}
    weathers = {json.loads(line)["id"]: json.loads(line) for line in WEATHER.read_text().splitlines()}
    played = {v: [] for v in BUNDLES}
    for name in sweeps:
        played[version_of(json.loads((runs_dir / name / "sweep.json").read_text()))].append(runs_dir / name)
    files: dict[str, bytes] = {}
    for v, bundle_name in BUNDLES.items():
        bundle = out / "bundles" / bundle_name
        shutil.rmtree(bundle, ignore_errors=True)
        tasks.generate(EVAL_PACK, bundle, live=v != "v1", marine=v == "v3", wind=v == "v4")
        scored = [(d, [r["instance"] for r in results(d) if r["outcome"] == "scored"]) for d in played[v]]
        hub_files, episode_ids = agentenv_files(bundle_name, bundle, scored)
        files |= hub_files
        by_ref = {r["task_id"]: r for r in refs.get(v, [])}
        files[f"tasks/{v}.parquet"] = table_bytes([task_row(by_version[v][i], v, by_ref.get(i), raw[v][i], weathers)
                                                   for i in ids[v]])
        episodes = [row for d in played[v] for row in episode_rows(d, v, by_version[v], episode_ids)]
        files[f"episodes/{v}.parquet"] = table_bytes(sorted(episodes, key=lambda r: (r["model"], r["task_id"])))
        if v in REFERENCE_FILES:
            ref_name, source = REFERENCE_FILES[v]
            files[f"references/{ref_name}.jsonl"] = source.read_bytes()
            files[f"references/{ref_name}.parquet"] = table_bytes([reference_row(r) for r in refs[v]])
        for d in played[v]:
            for path in sorted(d.rglob("*")):
                rel = path.relative_to(d)
                if path.is_file() and rel.parts[0] not in ("logs", "bundle"):
                    files[f"runs/{d.name}/{rel.as_posix()}"] = path.read_bytes()
    return files | {"README.md": card_text(plugin).encode()}


def write(files: dict[str, bytes], out: Path) -> None:
    for folder in ("tasks", "episodes", "references", "raw", "runs", "bundles"):
        shutil.rmtree(out / folder, ignore_errors=True)
    for path, content in files.items():
        (out / path).parent.mkdir(parents=True, exist_ok=True)
        (out / path).write_bytes(content)


def push(out: Path, repo: str, tag: str | None, message: str) -> str:
    """The folder as one commit on top of the repo's current commit, deleting the files this build no longer writes;
    a concurrent push makes it fail rather than interleave."""
    api = HfApi()
    parent = api.repo_info(repo, repo_type="dataset").sha
    paths = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    stale = [p for p in api.list_repo_files(repo, repo_type="dataset", revision=parent)
             if p not in paths and p != ".gitattributes"]
    operations = [CommitOperationAdd(p, out / p) for p in paths] + [CommitOperationDelete(p) for p in stale]
    commit = api.create_commit(repo, operations, repo_type="dataset", parent_commit=parent, commit_message=message)
    if tag:
        api.create_tag(repo, tag=tag, repo_type="dataset", revision=commit.oid)
    return commit.commit_url


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("sweeps", nargs="*", default=SWEEPS)
    ap.add_argument("--runs", type=Path, default=RUNS)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--plugin-ref", default=f"v{VERSION}",
                    help="The plugin tag the card's bundles pin, for agent-env hf run.")
    ap.add_argument("--repo", help="Push the folder to this dataset repo after writing it.")
    ap.add_argument("--tag", help="Tag the pushed commit, e.g. v0.4.0.")
    ap.add_argument("--message", default="Publish PortSimEnv on AgentEnv")
    args = ap.parse_args()
    plugin = f"agentenv-portsim @ git+https://github.com/earakely-scale/agentenv-portsim-plugin@{args.plugin_ref}"
    with namespace_routing():
        files = build(args.sweeps, args.runs, args.out, plugin)
    scan(files, known_values())
    write(files, args.out)
    counts = {p: pq.read_metadata(io.BytesIO(c)).num_rows for p, c in files.items() if p.endswith(".parquet")}
    print("\n".join(f"{n:6} {p}" for p, n in sorted(counts.items())), f"\ninto {args.out}")
    if args.repo:
        print(push(args.out, args.repo, args.tag, args.message))


if __name__ == "__main__":
    main()
