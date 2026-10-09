"""Build the Hugging Face dataset earakely-scale/PortSimEnv-AgentEnv from this checkout and recorded sweeps: the v3, v2
and v1 task tables, the episode tables with each transcript inline, the agent-env bundles, the live and marine
references, and the raw runs the replay Space reads. The dataset card (README.md) is written by hand and left in place.
Last, every file in the folder goes through agentenv-hf's check for keys and token shapes, so the build fails before
anything is uploaded.

    uv run python scripts/hub_dataset.py --out hub/dataset g2 live-pilot-gpt live-gpt live-pilot-sonnet live-sonnet \\
        marine-pilot-gpt marine-gpt marine-pilot-sonnet marine-sonnet
"""

import argparse
import json
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from agentenv_hf.scan import known_values, scan

from agentenv_portsim import marine, tasks
from agentenv_portsim.schedule import MARINE_ENV, schedule
from agentenv_portsim.sweep import EVAL_PACK, RUNS, results

NAMES = {"openai/gpt-6.1-sol": "GPT-6.1 Sol", "anthropic/claude-sonnet-5-5": "Claude Sonnet 5.5"}


def play_step(task, version: str) -> dict:
    task_steps = {"v1": lambda: tasks.steps(task, 5.0), "v2": lambda: tasks.live_steps(task, 5.0),
                  "v3": lambda: tasks.live_steps(task, 5.0, env=MARINE_ENV, week=marine.MarineWeek)}[version]()
    return next(s for s in task_steps if s["id"] == "play")


def task_row(task, version: str, reference: dict | None, raw: str) -> dict:
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
    if version == "v3":
        pools = task.rules["marine"]
        row |= {"v2_optimal_cost": reference["v2_optimal_cost"], "pilots": pools["pilots"], "tugs": pools["tugs"],
                "other_movements": len(pools["movements"])}
    return row | {"watches": json.dumps([{"watch": w.index, "hour": w.hour,
                                          "notices": [{"from": n.name, "about_hour": n.event_hour, "text": n.text}
                                                      for n in w.notices]} for w in watches], ensure_ascii=False),
                  "task": raw}


def episode_rows(sweep_dir: Path, live: bool, by_id: dict) -> list[dict]:
    rows = []
    for r in results(sweep_dir):
        if r["outcome"] != "scored":
            continue
        record = json.loads((sweep_dir / r["transcript"]).read_text())
        task = by_id[r["task_id"]]
        row = {"model": r["model"], "model_name": NAMES.get(r["model"], r["model"]), "task_id": r["task_id"],
               "difficulty": task.difficulty, "quay": task.quay, "num_ships": len(task.ships), "reward": r["reward"],
               "feasible": r["feasible"], "cost": r["plan_cost"], "optimal_cost": r["optimal_cost"],
               "turns": r["turns"], "tool_calls": r["tool_calls"], "input_tokens": r["input_tokens"],
               "output_tokens": r["output_tokens"], "cost_usd": r["cost_usd"], "end_reason": r["end_reason"],
               "sweep": sweep_dir.name}
        if live:
            row |= {"num_watches": r["watches"], "regret": r["regret"], "excused_cost": r["excused_cost"]}
        else:
            row |= {"submitted": r["submitted"], "checks": r["checks"]}
        rows.append(row | {"final_plan": json.dumps(record["final"].get("plan")),
                           "steps": json.dumps(record["steps"], ensure_ascii=False),
                           "messages": json.dumps(record["messages"], ensure_ascii=False)})
    return rows


def reference_row(r: dict) -> dict:
    flat = {"task_id": r["task_id"], "qualifies": r["qualifies"], "optimal_cost": r["optimal_cost"],
            "unavoidable_cost": r["unavoidable_cost"], "watch_hours": r["watch_hours"]}
    if "v2_optimal_cost" in r:
        flat["v2_optimal_cost"] = r["v2_optimal_cost"]
    for policy in ("rolling", "naive"):
        flat |= {f"{policy}_{k}": r[policy][k] for k in ("cost", "reward", "feasible", "excused_cost")}
    return flat | {"rolling_plans": json.dumps(r["rolling"]["plans"]), "configs": json.dumps(r["configs"]),
                   "solver": json.dumps(r["solver"])}


def write(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), path)


def raw_lines(pack_dir: Path) -> dict[str, str]:
    return {json.loads(line)["task_id"]: line for line in (pack_dir / "tasks.jsonl").read_text().splitlines()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sweeps", nargs="+")
    ap.add_argument("--runs", type=Path, default=RUNS)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    pack = tasks.pack_tasks(EVAL_PACK)
    by_id = {t.task_id: t for t in pack}
    raw = raw_lines(tasks.PACKS / EVAL_PACK)
    live_refs = {r["task_id"]: r for r in tasks.live_references()}
    marine_pack, marine_raw = marine.pack(), raw_lines(marine.pack_dir())
    marine_refs = {r["task_id"]: r for r in marine.references()}
    write([task_row(marine_pack.get(i), "v3", marine_refs[i], marine_raw[i]) for i in marine.task_ids()],
          args.out / "tasks/v3.parquet")
    write([task_row(by_id[i], "v2", live_refs[i], raw[i]) for i in tasks.live_task_ids()],
          args.out / "tasks/v2.parquet")
    write([task_row(t, "v1", None, raw[t.task_id]) for t in pack], args.out / "tasks/v1.parquet")
    episodes = {"v3": [], "v2": [], "v1": []}
    for name in args.sweeps:
        sweep = json.loads((args.runs / name / "sweep.json").read_text())
        version = "v3" if sweep.get("marine") else "v2" if sweep.get("live") else "v1"
        episodes[version] += episode_rows(args.runs / name, version != "v1", by_id)
        shutil.rmtree(args.out / "runs" / name, ignore_errors=True)
        shutil.copytree(args.runs / name, args.out / "runs" / name, ignore=shutil.ignore_patterns("logs", "bundle"))
    for version, rows in episodes.items():
        write(sorted(rows, key=lambda r: (r["model"], r["task_id"])), args.out / f"episodes/{version}.parquet")
    shutil.rmtree(args.out / "bundles", ignore_errors=True)
    tasks.generate(EVAL_PACK, args.out / "bundles/dock-v1-eval-marine", marine=True)
    tasks.generate(EVAL_PACK, args.out / "bundles/dock-v1-eval-live", live=True)
    tasks.generate(EVAL_PACK, args.out / "bundles/dock-v1-eval")
    (args.out / "references").mkdir(parents=True, exist_ok=True)
    for name, source, refs in (("live", tasks.REFERENCES, tasks.live_references()),
                               ("marine", marine.REFERENCES, marine.references())):
        shutil.copy(source, args.out / f"references/{name}.jsonl")
        write([reference_row(r) for r in refs], args.out / f"references/{name}.parquet")
    scan({p.relative_to(args.out).as_posix(): p.read_bytes() for p in sorted(args.out.rglob("*")) if p.is_file()},
         known_values())
    print(", ".join(f"{len(rows)} {version} episodes" for version, rows in episodes.items()), f"into {args.out}")


if __name__ == "__main__":
    main()
