"""Build the Hugging Face dataset earakely-scale/PortSimEnv-AgentEnv from this checkout and recorded sweeps: the v2 and
v1 task tables, the episode tables with each transcript inline, the agent-env bundles, the live references, and the
raw runs the replay Space reads. The dataset card (README.md) is written by hand and left in place.

    uv run python scripts/hub_dataset.py --out hub/dataset g2 live-pilot-gpt live-gpt live-pilot-sonnet live-sonnet
"""

import argparse
import json
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from agentenv_portsim import tasks
from agentenv_portsim.schedule import schedule
from agentenv_portsim.sweep import EVAL_PACK, RUNS, results

NAMES = {"openai/gpt-6.1-sol": "GPT-6.1 Sol", "anthropic/claude-sonnet-5-5": "Claude Sonnet 5.5"}


def task_row(task, live: bool, reference: dict | None, raw: str) -> dict:
    play = next(s for s in (tasks.live_steps if live else tasks.steps)(task, 5.0) if s["id"] == "play")
    row = {"task_id": task.task_id, "quay": task.quay, "terminal": task.terminal, "difficulty": task.difficulty,
           "week": task.week, "week_start_utc": task.week_start_utc, "num_ships": len(task.ships),
           "num_disruptions": len(task.disruptions), "system_prompt": play["system_prompt"],
           "situation": play["prompt"], "optimal_cost": task.reference["optimal_cost"]}
    if live:
        watches = schedule(task)
        row |= {"num_watches": len(watches), "unavoidable_cost": reference["unavoidable_cost"],
                "rolling_cost": reference["rolling"]["cost"], "naive_cost": reference["naive"]["cost"],
                "watches": json.dumps([{"watch": w.index, "hour": w.hour,
                                        "notices": [{"from": n.name, "about_hour": n.event_hour, "text": n.text}
                                                    for n in w.notices]} for w in watches], ensure_ascii=False)}
    else:
        row |= {"naive_cost": task.reference["naive_cost"], "proven_optimal": task.reference["proven_optimal"],
                "optimal_plan": json.dumps(task.reference["optimal_plan"]),
                "naive_plan": json.dumps(task.reference["naive_plan"])}
    return row | {"task": raw}


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


def write(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sweeps", nargs="+")
    ap.add_argument("--runs", type=Path, default=RUNS)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    pack = tasks.pack_tasks(EVAL_PACK)
    by_id = {t.task_id: t for t in pack}
    references = {r["task_id"]: r for r in tasks.live_references()}
    lines = (tasks.PACKS / EVAL_PACK / "tasks.jsonl").read_text().splitlines()
    raw = {json.loads(line)["task_id"]: line for line in lines}
    live_ids = tasks.live_task_ids()
    write([task_row(by_id[i], True, references[i], raw[i]) for i in live_ids], args.out / "tasks/v2.parquet")
    write([task_row(t, False, None, raw[t.task_id]) for t in pack], args.out / "tasks/v1.parquet")
    episodes = {"v2": [], "v1": []}
    for name in args.sweeps:
        live = json.loads((args.runs / name / "sweep.json").read_text()).get("live", False)
        episodes["v2" if live else "v1"] += episode_rows(args.runs / name, live, by_id)
        shutil.rmtree(args.out / "runs" / name, ignore_errors=True)
        shutil.copytree(args.runs / name, args.out / "runs" / name, ignore=shutil.ignore_patterns("logs", "bundle"))
    for version, rows in episodes.items():
        write(sorted(rows, key=lambda r: (r["model"], r["task_id"])), args.out / f"episodes/{version}.parquet")
    shutil.rmtree(args.out / "bundles", ignore_errors=True)
    tasks.generate(EVAL_PACK, args.out / "bundles/dock-v1-eval-live", live=True)
    tasks.generate(EVAL_PACK, args.out / "bundles/dock-v1-eval")
    (args.out / "references").mkdir(parents=True, exist_ok=True)
    shutil.copy(tasks.REFERENCES, args.out / "references/live.jsonl")
    print(f"{len(live_ids)} v2 and {len(pack)} v1 tasks, {len(episodes['v2'])} v2 and {len(episodes['v1'])} v1 "
          f"episodes into {args.out}")


if __name__ == "__main__":
    main()
