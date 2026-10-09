"""Recorded runs copied unchanged from results/runs: v1 g2 (a scored week, a week with no plan, a retried week) and two
live weeks, one with get_time calls. marine_runs holds a synthetic marine run, made in process with no model: the film
week played through the env's tools on a MarineWeek by the stored rolling re-plans and by the naive policy, as
marine_references.py plays them; marine_run() rebuilds it. wind_runs holds a synthetic wind run made the same way on
the wind fixtures (synthetic weather): their storm week played on a WindWeek by the stored forecast-following and
forecast-blind re-plans; wind_run() rebuilds it."""

import json
from pathlib import Path

from berth_core import TaskPack, plan_from_list, plan_to_list

from agentenv_portsim import marine, tasks
from agentenv_portsim.live import _json
from agentenv_portsim.marine import MarineWeek
from agentenv_portsim.sweep import slug
from agentenv_portsim.wind import WindWeek
from agentenv_portsim.world import Week, naive

ROOT = Path(__file__).resolve().parent / "runs"
MARINE_ROOT = Path(__file__).resolve().parent / "marine_runs"
WIND_ROOT = Path(__file__).resolve().parent / "wind_runs"
WIND_FIXTURES = Path(__file__).resolve().parents[1] / "wind" / "fixtures"
SONNET, GPT = "anthropic/claude-sonnet-5-5", "openai/gpt-6.1-sol"
LIVE = [("live-sonnet", SONNET, "dock-24B-w06x1-busy-0"), ("live-gpt", GPT, "dock-36A-w06x1-standard-0")]
MARINE_RUN, MARINE_TASK = "marine-scripted", "dock-24B-w07x1-busy-0"
WIND_RUN, WIND_TASK = "wind-scripted", "dock-24B-w07x1-busy-0-e00"


def stored(mode: str):
    return mode, lambda week, ref: plan_from_list(ref[mode]["plans"][week.watch])


POLICIES = {"scripted/naive": ("naive", lambda week, ref: naive(week)), "scripted/rolling": stored("rolling")}
WIND_POLICIES = {"scripted/blind": stored("blind"), "scripted/rolling": stored("rolling")}
STEPS = ("check_plan", "confirm_berths", "advance")
GRADE = ("cost", "reward", "feasible", "excused_cost")


def scored(run: str, task_id: str) -> dict:
    rows = [json.loads(line) for line in (ROOT / run / "results.jsonl").read_text().splitlines()]
    return next(r for r in rows if r["task_id"] == task_id and r["outcome"] == "scored")


def transcript(run: str, task_id: str) -> dict:
    return json.loads((ROOT / run / scored(run, task_id)["transcript"]).read_text())


def _tool(week: Week, name: str, args: dict) -> str:
    """The env tool's reply (live.py), the call counted as LiveEpisode counts it; after an advance the watch's
    triggers deliver its notices, as port_notice does."""
    week.calls += 1
    if name == "get_situation":
        result = week.situation()
    elif name == "check_plan":
        result = week.check(args["plan"])
    elif name == "confirm_berths":
        result = week.confirm(args["plan"])
    else:
        result = week.finish("done") if week.last else week.open()
    out = _json({**result, "messages": week.drain()})
    if name == "advance" and not week.done:
        for n in week.watches[week.watch].notices:
            week.notice(n.event_id, n.name, n.text, "trigger")
    return out


def _episode(sweep: str, week: Week, ref: dict, model: str, policies: dict, out: Path,
             rules: str = tasks.LIVE_RULES) -> dict:
    """Each watch: check and confirm the windows the policy changes, then advance. Writes the transcript under ``out``
    and returns the attempt's row, as a live sweep records them."""
    key, policy = policies[model]
    task = week.task
    record = {"model": model, "messages": [
        {"role": "system", "content": tasks.live_rules(task, rules)},
        {"role": "user", "content": tasks.LIVE_OPENING.format(situation=week.situation()["situation"])}],
        "steps": [], "final": {"submitted": False, "plan": None}, "reward": 0.0,
        "usage": {"input_tokens": 0, "output_tokens": 0}, "turns": 0, "end_reason": None, "errors": []}

    def turn(calls: list[tuple[str, dict]]) -> None:
        record["turns"] += 1
        ids = [(f"call-{record['turns']}-{k}", name, args) for k, (name, args) in enumerate(calls)]
        record["messages"].append({"role": "assistant", "content": "", "reasoning": "", "stop": "tool_use",
                                   "tool_calls": [{"id": i, "name": name, "arguments": json.dumps(args)}
                                                  for i, name, args in ids]})
        for i, name, args in ids:
            out = _tool(week, name, args)
            if name in STEPS:
                record["steps"].append({"turn": record["turns"], "tool": name, "plan": args.get("plan"),
                                        "result": json.loads(out)})
            record["messages"].append({"role": "tool", "tool_call_id": i, "name": name, "content": out})

    turn([("get_situation", {})])
    while not week.done:
        target = policy(week, ref)
        rows = [r for r in plan_to_list(target) if week.plan.get(r["ship"]) != target[r["ship"]]]
        if rows:
            turn([("check_plan", {"plan": rows})])
        turn([("confirm_berths", {"plan": rows})] * bool(rows) + [("advance", {})]
             + [("get_situation", {})] * (not week.last))
    g, episode = week.grade, week.data()
    assert {k: g[k] for k in GRADE} == {k: ref[key][k] for k in GRADE}
    record |= {"reward": g["reward"], "end_reason": "done", "seconds": 0.0}
    path = Path("transcripts") / slug(model) / f"{task.task_id}-r1-a1.json"
    (out / path).parent.mkdir(parents=True, exist_ok=True)
    (out / path).write_text(_json(record))
    return {"sweep": sweep, "model": model, "task_id": task.task_id, "rep": 1, "attempt": 1,
            "started_utc": "2026-10-07T00:00:00Z", "wall_seconds": 0.0, "exit": 0,
            "instance": f"in-process/{sweep}/{task.task_id}-{key}", "outcome": "scored", "failed_step": None,
            "error_code": None, "error": None, "retryable": False, "reward": g["reward"], "submitted": True,
            "feasible": g["feasible"], "plan_cost": g["cost"], "optimal_cost": g["optimal_cost"],
            "checks": sum(episode["planning_calls"]), "calls": episode["calls_used"], "end_reason": "done",
            "turns": record["turns"], "tool_calls": week.calls, "input_tokens": 0, "output_tokens": 0,
            "cached_tokens": 0, "cache_write_tokens": 0, "cost_usd": 0.0, "agent_reward": g["reward"],
            "transcript": path.as_posix(), "watches": episode["watches"], "excused_cost": g["excused_cost"],
            "regret": g["regret"]}


def _sweep(out: Path, spec: dict, rows: list[dict]) -> None:
    (out / "sweep.json").write_text(json.dumps(spec, indent=2) + "\n")
    (out / "results.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))


def marine_run(root: Path) -> None:
    out = root / MARINE_RUN
    task = marine.pack().get(MARINE_TASK)
    ref = next(r for r in marine.references() if r["task_id"] == MARINE_TASK)
    rows = [_episode(MARINE_RUN, MarineWeek(task), ref, model, POLICIES, out) for model in POLICIES]
    _sweep(out, {"name": MARINE_RUN, "models": list(POLICIES), "tasks": [MARINE_TASK], "k": 1, "episode_cap_usd": 5.0,
                 "live": True, "marine": True}, rows)


def wind_fixture() -> tuple[TaskPack, dict[str, dict]]:
    """The wind fixtures (tests/wind_fixtures.py) as wind.pack() and wind.references() read them."""
    refs = map(json.loads, (WIND_FIXTURES / "wind" / "references.jsonl").read_text().splitlines())
    return TaskPack(WIND_FIXTURES / "dock-v1-wind"), {r["task_id"]: r for r in refs}


def wind_run(root: Path, task_ids: tuple[str, ...] = (WIND_TASK,)) -> None:
    out, (pack, refs) = root / WIND_RUN, wind_fixture()
    rows = [_episode(WIND_RUN, WindWeek(pack.get(t)), refs[t], model, WIND_POLICIES, out, tasks.WIND_RULES)
            for model in WIND_POLICIES for t in task_ids]
    _sweep(out, {"name": WIND_RUN, "models": list(WIND_POLICIES), "tasks": list(task_ids), "k": 1,
                 "episode_cap_usd": 5.0, "live": True, "wind": True}, rows)


if __name__ == "__main__":
    marine_run(MARINE_ROOT)
    wind_run(WIND_ROOT)
