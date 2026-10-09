"""Build the Hugging Face dataset earakely-scale/PortSimEnv-AgentEnv from this checkout and the recorded sweeps, and
push it. Two kinds of tables share the repo:

- PortSim's, one family per version (v4 wind, v3 marine, v2 live, v1): the weeks with what the agent is told and the
  reference costs, the recorded runs with their grades and chat transcripts, and the references. Beside them, each
  model's results per version, as a table, as the card's tables and as a board.json in the shape of PortSimEnv's.
- agentenv-hf's, one per bundle, as `agent-env hf publish` writes them: the bundle's tasks and runs, each run's record
  and native trajectory, and the bundle itself, which `agent-env hf run` runs. A version's runs come from several
  sweeps, each played from a bundle of its own, so they are built sweep by sweep and joined under the version's
  bundle name.

The card is hub/dataset/README.md, with each bundle's configs and needs added by agentenv-hf's card writer. The runs
are read from results/runs and from the agent-env stores the sweeps wrote them to. Every file goes through
agentenv-hf's check for keys and token shapes before anything is written, and --repo pushes the folder as one commit
on top of the commit it read, removing what the build no longer writes.

    uv run python scripts/hub_dataset.py --out build/hub/dataset
    uv run python scripts/hub_dataset.py --out build/hub/dataset --repo earakely-scale/PortSimEnv-AgentEnv --tag v0.4.3
"""

import argparse
import io
import json
import re
import shutil
import statistics
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
from agentenv_portsim.sweep import EVAL_PACK, RUNS, TIERS, ci, results

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "hub/dataset/README.md"
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
WEATHER = ROOT / "data/wind/weather.jsonl"
SPLIT = "eval"
BOARD = ["gpt", "sonnet", "opus", "haiku", "astra", "luna", "kimi", "glm", "glmflash", "qwen2t", "qwen27b", "dsflash"]
SWEEPS = [f"{env}-{stage}{model}{replay}" for env in ("wind", "marine", "live") for model in BOARD
          for stage in ("pilot-", "") for replay in ("", "-2", "-3")]  # replays of runs left unscored
SWEEPS.append("g2")
BUNDLES = {"v4": f"{EVAL_PACK}-wind", "v3": f"{EVAL_PACK}-marine", "v2": f"{EVAL_PACK}-live", "v1": EVAL_PACK}
REFERENCE_FILES = {"v4": ("wind", wind.REFERENCES), "v3": ("marine", marine.REFERENCES),
                   "v2": ("live", tasks.REFERENCES)}
SETUP = "agent-env portsim setup --agent"
ENVS = {"v4": WIND_ENV, "v3": MARINE_ENV, "v2": "portsim-live", "v1": "portsim"}
NAMES = {
    "anthropic/claude-opus-5-5": "Claude Opus 5.5", "anthropic/claude-sonnet-5-5": "Claude Sonnet 5.5",
    "anthropic/claude-haiku-5-5": "Claude Haiku 5.5", "openai/gpt-6-astra": "GPT-6 Astra",
    "openai/gpt-6.1-sol": "GPT-6.1 Sol", "openai/gpt-6-luna": "GPT-6 Luna", "fireworks_ai/kimi-k3": "Kimi K3",
    "fireworks_ai/glm-5p3": "GLM-5.3", "fireworks_ai/glm-5p3-flash": "GLM-5.3-Flash",
    "fireworks_ai/qwen3p8-2p4t-a95b": "Qwen3.8-2.4T", "groq/qwen/qwen3.8-27b": "Qwen3.8-27B",
    "fireworks_ai/deepseek-v4p1-flash": "DeepSeek V4.1 Flash",
}
PROVIDERS = {"anthropic": "Anthropic", "openai": "Azure OpenAI", "fireworks_ai": "Fireworks", "groq": "Groq"}
BOARD_TABLE = re.compile(r"(<!-- board:(v\d|all) -->\n).*?(\n<!-- /board:\2 -->)", re.S)
LIVE_VERSIONS = ("v4", "v3", "v2")
VERSION_NAMES = {"v4": "the wind port", "v3": "the marine port", "v2": "the live port"}
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


def episode_rows(sweep_dir: Path, version: str, by_id: dict, episode_ids: dict[str, str],
                 graded: dict[str, list]) -> list[dict]:
    """One row per scored run. A v1 run's final plan is the one it submitted; a live run's is the windows it confirmed,
    as the verifier graded them."""
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
               "output_tokens": r["output_tokens"], "cost_usd": r["cost_usd"], "seconds": r["wall_seconds"],
               "end_reason": r["end_reason"], "sweep": sweep_dir.name}
        if version == "v1":
            row |= {"submitted": r["submitted"], "checks": r["checks"]}
        else:
            row |= {"reached_end": r["submitted"], "num_watches": r["watches"], "regret": r["regret"],
                    "excused_cost": r["excused_cost"]}
        plan = record["final"].get("plan") if version == "v1" else graded.get(row["episode_id"])
        rows.append(row | {"final_plan": json.dumps(plan),
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


def board(version: str, episodes: list[dict]) -> list[dict]:
    """One row per model, best first: the mean over its weeks with the bootstrap CI the sweep reports use, drawing the
    weeks in task id order as they do, each tier's mean, and the counts PortSimEnv's eval board shows. A week played
    more than once counts as its runs' mean."""
    rows = []
    for model in dict.fromkeys(e["model"] for e in episodes):
        eps = [e for e in episodes if e["model"] == model]
        weeks: dict[str, list[dict]] = {}
        for e in eps:
            weeks.setdefault(e["task_id"], []).append(e)
        mean = {t: statistics.mean(e["reward"] for e in weeks[t]) for t in sorted(weeks)}
        low, high = ci(list(mean.values()))
        tiers = {t: statistics.mean(m for w, m in mean.items() if weeks[w][0]["difficulty"] == t)
                 for t in TIERS if any(es[0]["difficulty"] == t for es in weeks.values())}
        costs = [e["cost_usd"] for e in eps if e["cost_usd"] is not None]
        rows.append({
            "version": version, "env": ENVS[version], "model": model, "model_name": NAMES.get(model, model),
            "provider": PROVIDERS.get(model.split("/")[0], model.split("/")[0]), "weeks": len(weeks), "runs": len(eps),
            "mean_reward": statistics.mean(mean.values()), "ci_low": low, "ci_high": high,
            **{f"reward_{t}": m for t, m in tiers.items()},
            "finished": sum(bool(e.get("reached_end", e.get("submitted"))) for e in eps),
            "feasible": sum(bool(e["feasible"]) for e in eps),
            "optimal": sum(bool(e["feasible"]) and e["cost"] <= e["optimal_cost"] for e in eps),
            "median_turns": statistics.median(e["turns"] for e in eps),
            "input_tokens": sum(e["input_tokens"] or 0 for e in eps),
            "output_tokens": sum(e["output_tokens"] or 0 for e in eps),
            "cost_usd": sum(costs), "cost_per_episode": statistics.mean(costs) if costs else None,
            "median_seconds": statistics.median(e["seconds"] for e in eps if e["seconds"] is not None),
        })
    return sorted(rows, key=lambda r: -r["mean_reward"])


def board_json(version: str, rows: list[dict], weeks: int) -> dict:
    """The board in the shape of PortSimEnv's article data (portsim-results.json), with the CI, provider and cost."""
    return {"version": version, "env": ENVS[version], "tasks": weeks, "board": [{
        "model": r["model_name"], "key": r["model"], "provider": r["provider"], "n": r["runs"],
        "mean": round(r["mean_reward"], 4), "ci": [round(r["ci_low"], 4), round(r["ci_high"], 4)],
        "tiers": {t: round(r[f"reward_{t}"], 4) for t in TIERS if f"reward_{t}" in r},
        "submitted": r["finished"], "feasible": r["feasible"], "optimal": r["optimal"],
        "tokens_out": r["output_tokens"], "tokens_in": r["input_tokens"], "median_s": round(r["median_seconds"]),
        "cost_usd": round(r["cost_usd"], 2)} for r in rows]}


def board_markdown(version: str, rows: list[dict], weeks: int) -> str:
    finished = "Submitted" if version == "v1" else "Reached the end"
    optimal = "At the anchor" if version == "v4" else "Optimal"
    tiers = [t for t in TIERS if any(f"reward_{t}" in r for r in rows)]
    lines = [f"| Model | Provider | Weeks | Mean reward (95% CI) | {' | '.join(t.capitalize() for t in tiers)} "
             f"| {finished} | Feasible | {optimal} | Median turns | Cost per episode |",
             "|---|---|---:|---|" + "---:|" * (len(tiers) + 5)]
    for r in rows:
        lines.append(" | ".join([
            f"| {r['model_name']}", r["provider"], f"{r['weeks']} of {weeks}",
            f"**{r['mean_reward']:.3f}** ({r['ci_low']:.3f} to {r['ci_high']:.3f})",
            *(f"{r[f'reward_{t}']:.3f}" if f"reward_{t}" in r else "–" for t in tiers),
            str(r["finished"]), str(r["feasible"]), str(r["optimal"]), f"{r['median_turns']:g}",
            f"${r['cost_per_episode']:.2f}" if r["cost_per_episode"] is not None else "–"]) + " |")
    return "\n".join(lines)


def summary_markdown(rows: list[dict]) -> str:
    """Each model on every live version: its mean on each and over all their weeks, each week weighing the same, best
    first; only models that played all of them."""
    by: dict[str, dict[str, dict]] = {}
    for r in rows:
        if r["version"] in LIVE_VERSIONS:
            by.setdefault(r["model"], {})[r["version"]] = r
    full = {m: v for m, v in by.items() if set(v) == set(LIVE_VERSIONS)}

    def mean(v: dict) -> float:
        return sum(r["mean_reward"] * r["weeks"] for r in v.values()) / sum(r["weeks"] for r in v.values())

    lines = ["| Model | Provider | " + " | ".join(f"{v}, {VERSION_NAMES[v]}" for v in LIVE_VERSIONS)
             + " | All weeks | Feasible weeks |", "|---|---|" + "---:|" * (len(LIVE_VERSIONS) + 2)]
    for v in sorted(full.values(), key=lambda v: -mean(v)):
        first = v[LIVE_VERSIONS[0]]
        lines.append(" | ".join([
            f"| {first['model_name']}", first["provider"], *(f"{v[x]['mean_reward']:.3f}" for x in LIVE_VERSIONS),
            f"**{mean(v):.3f}**",
            f"{sum(r['feasible'] for r in v.values())} of {sum(r['weeks'] for r in v.values())}"]) + " |")
    return "\n".join(lines)


def raw_lines(pack_dir: Path) -> dict[str, str]:
    return {json.loads(line)["task_id"]: line for line in (pack_dir / "tasks.jsonl").read_text().splitlines()}


def agentenv_files(name: str, bundle: Path,
                   sweeps: list[tuple[Path, list[str]]]) -> tuple[dict[str, bytes], dict, dict]:
    """agentenv-hf's files for the bundle ``name``: its tasks from ``bundle``, and the runs ``sweeps`` list by instance
    id, each sweep built from its own bundle under ``name``. Returns the files, each instance's episode id, and each
    episode's plan as its verifier graded it."""
    files = dataset.build(runs.locate(str(bundle)), name=name, split=SPLIT, which="latest").files
    parts, raw, episode_ids, graded = [], {}, {}, {}
    for sweep_dir, ids in sweeps:
        played = runs.locate(str(sweep_dir / "bundle"))
        built = dataset.build(played, name=name, split=SPLIT, which="latest", instance_ids=tuple(ids)).files
        parts.append(pq.read_table(io.BytesIO(built[f"episodes/{name}.parquet"])))
        for line in built[f"raw/{name}.jsonl"].decode().splitlines():
            run = json.loads(line)
            raw[run["episode_id"]] = line
            outcome = run["record"]["metadata"]["verifications"]["portsim"]["results"]
            graded[run["episode_id"]] = outcome[0]["episode"].get("plan")
        rewrite = records.Rewrite(played.id_root, name)
        episode_ids |= {i: rewrite.text(i) for i in ids}
    episodes = pa.concat_tables(parts).sort_by([("model", "ascending"), ("task", "ascending")])
    sink = io.BytesIO()
    pq.write_table(episodes, sink)
    files[f"episodes/{name}.parquet"] = sink.getvalue()
    files[f"raw/{name}.jsonl"] = "".join(raw[i] + "\n" for i in episodes.column("episode_id").to_pylist()).encode()
    return files, episode_ids, graded


def card_text(plugin: str, boards: dict[str, str] | None = None) -> str:
    """hub/dataset/README.md with each version's board between its markers, and each bundle's two configs and its
    needs, as agentenv-hf's publish writes them."""
    text = BOARD_TABLE.sub(lambda m: m[1] + (f"\n{t}\n" if (t := (boards or {}).get(m[2])) else "") + m[3],
                           CARD.read_text())
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
    boards: dict[str, str] = {}
    board_rows: list[dict] = []
    for name in sweeps:
        played[version_of(json.loads((runs_dir / name / "sweep.json").read_text()))].append(runs_dir / name)
    files: dict[str, bytes] = {}
    for v, bundle_name in BUNDLES.items():
        bundle = out / "bundles" / bundle_name
        shutil.rmtree(bundle, ignore_errors=True)
        tasks.generate(EVAL_PACK, bundle, live=v != "v1", marine=v == "v3", wind=v == "v4")
        scored = [(d, [r["instance"] for r in results(d) if r["outcome"] == "scored"]) for d in played[v]]
        scored = [(d, instances) for d, instances in scored if instances]
        hub_files, episode_ids, graded = agentenv_files(bundle_name, bundle, scored)
        files |= hub_files
        by_ref = {r["task_id"]: r for r in refs.get(v, [])}
        files[f"tasks/{v}.parquet"] = table_bytes([task_row(by_version[v][i], v, by_ref.get(i), raw[v][i], weathers)
                                                   for i in ids[v]])
        episodes = [row for d in played[v] for row in episode_rows(d, v, by_version[v], episode_ids, graded)]
        files[f"episodes/{v}.parquet"] = table_bytes(sorted(episodes, key=lambda r: (r["model"], r["task_id"])))
        if episodes:
            rows = board(v, episodes)
            weeks = len({e["task_id"] for e in episodes})
            board_rows += rows
            boards[v] = board_markdown(v, rows, weeks)
            files[f"results/{v}.json"] = (json.dumps(board_json(v, rows, weeks), indent=1) + "\n").encode()
        if v in REFERENCE_FILES:
            ref_name, source = REFERENCE_FILES[v]
            files[f"references/{ref_name}.jsonl"] = source.read_bytes()
            files[f"references/{ref_name}.parquet"] = table_bytes([reference_row(r) for r in refs[v]])
        for d in played[v]:
            for path in sorted(d.rglob("*")):
                rel = path.relative_to(d)
                if path.is_file() and rel.parts[0] not in ("logs", "bundle"):
                    files[f"runs/{d.name}/{rel.as_posix()}"] = path.read_bytes()
    files["results/board.parquet"] = table_bytes(board_rows)
    boards["all"] = summary_markdown(board_rows)
    return files | {"README.md": card_text(plugin, boards).encode()}


def write(files: dict[str, bytes], out: Path) -> None:
    for folder in ("tasks", "episodes", "references", "results", "raw", "runs", "bundles"):
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
    ap.add_argument("sweeps", nargs="*", help="Default: every sweep in SWEEPS that has been run.")
    ap.add_argument("--runs", type=Path, default=RUNS)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--plugin-ref", default=f"v{VERSION}",
                    help="The plugin tag the card's bundles pin, for agent-env hf run.")
    ap.add_argument("--repo", help="Push the folder to this dataset repo after writing it.")
    ap.add_argument("--tag", help="Tag the pushed commit, e.g. v0.4.3.")
    ap.add_argument("--message", default="Publish PortSimEnv on AgentEnv")
    args = ap.parse_args()
    plugin = f"agentenv-portsim @ git+https://github.com/earakely-scale/agentenv-portsim-plugin@{args.plugin_ref}"
    sweeps = args.sweeps or [s for s in SWEEPS if (args.runs / s / "sweep.json").is_file()]
    print("sweeps:", " ".join(sweeps))
    with namespace_routing():
        files = build(sweeps, args.runs, args.out, plugin)
    scan(files, known_values())
    write(files, args.out)
    counts = {p: pq.read_metadata(io.BytesIO(c)).num_rows for p, c in files.items() if p.endswith(".parquet")}
    print("\n".join(f"{n:6} {p}" for p, n in sorted(counts.items())), f"\ninto {args.out}")
    if args.repo:
        print(push(args.out, args.repo, args.tag, args.message))


if __name__ == "__main__":
    main()
