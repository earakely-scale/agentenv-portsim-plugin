"""Recorded sweep runs as the episode summaries and rollouts PortSimEnv's viewer reads: a v1 run regraded from its
final plan, a live run replayed through its Week from the recorded tool calls."""

import json
from dataclasses import dataclass
from pathlib import Path

import click
from pydantic import TypeAdapter

from berth_core import MOVE_PENALTY, Plan, PlanError, Task, TaskPack, evaluate, grade, parse_plan, plan_to_list

from . import tasks
from .live import WindowsArg, _json, _raw
from .schedule import FREEZE_HOURS, LIVE_ENV, TOOLS, label, virtual_time
from .sweep import EVAL_PACK, Sweep, results
from .world import Week, charge

ARGS = TypeAdapter(WindowsArg)
STEPS = ("check_plan", "confirm_berths", "advance")


class ReplayError(Exception):
    pass


@dataclass(frozen=True)
class Run:
    id: str
    sweep: Sweep
    rep: int
    dir: Path
    rows: dict[tuple[str, str], dict]


class Runs:
    """The scored attempt of each model and task in the sweeps under ``root``: one viewer run per sweep and rep."""

    def __init__(self, root: Path, names: list[str] | None = None):
        self.pack = TaskPack(tasks.PACKS / EVAL_PACK)
        self.references = {r["task_id"]: r for r in tasks.live_references()}
        self.runs: dict[str, Run] = {}
        self.rollouts: dict[tuple[str, str, str], dict] = {}
        for name in names or sorted(p.parent.name for p in root.glob("*/sweep.json")):
            path = root / name / "sweep.json"
            if not path.is_file():
                raise click.UsageError(f"no sweep {name!r}: {path} doesn't exist")
            sweep = Sweep(**json.loads(path.read_text()))
            scored = [r for r in results(root / name) if r["outcome"] == "scored"]
            for rep in range(1, sweep.k + 1):
                run_id = name if sweep.k == 1 else f"{name}.r{rep}"
                self.runs[run_id] = Run(run_id, sweep, rep, root / name,
                                        {(r["model"], r["task_id"]): r for r in scored if r["rep"] == rep})

    def tasks(self) -> list[dict]:
        ids = sorted({task_id for run in self.runs.values() for _, task_id in run.rows})
        return [{"task_id": t.task_id, "split": t.split, "quay": t.quay, "terminal": t.terminal, "week": t.week,
                 "difficulty": t.difficulty, "ships": len(t.ships), "disruptions": [e["type"] for e in t.disruptions]}
                for t in map(self.pack.get, ids)]

    def index(self) -> list[dict]:
        out = []
        for run_id, run in sorted(self.runs.items()):
            if episodes := self.episodes(run_id):
                out.append({"run": run_id, "models": sorted({e["model"] for e in episodes}),
                            "episodes": len(episodes),
                            "mean_reward": round(sum(e["reward"] for e in episodes) / len(episodes), 4),
                            "env": LIVE_ENV if run.sweep.live else "portsim", "sweep": run.sweep.name, "rep": run.rep,
                            "k": run.sweep.k, "episode_cap_usd": run.sweep.episode_cap_usd})
        return out

    def episodes(self, run_id: str) -> list[dict]:
        run = self.runs[run_id]
        return [self.summary(run, run.rows[key]) for key in sorted(run.rows)]

    def summary(self, run: Run, row: dict) -> dict:
        """upstream's summarize() (eval/run_eval.py), and the attempt's record; a live run's week too."""
        ro = self.rollout(run.id, row["model"], row["task_id"])
        task = self.pack.get(row["task_id"])
        g = ro["final"].get("grade") or {}
        tools = [s["tool"] for s in ro["steps"]]
        live = run.sweep.live
        out = {"model": row["model"], "task_id": task.task_id, "split": task.split, "difficulty": task.difficulty,
               "quay": task.quay, "ships": len(task.ships), "reward": ro["reward"],
               "submitted": bool(ro["final"]["submitted"]), "feasible": bool(g.get("feasible")), "cost": g.get("cost"),
               "optimal_cost": task.reference["optimal_cost"],
               "naive_cost": self.references[task.task_id]["naive"]["cost"] if live else task.reference["naive_cost"],
               "turns": ro["turns"], "checks": tools.count("check_plan"), "seconds": ro["seconds"],
               "input_tokens": ro["usage"]["input_tokens"], "output_tokens": ro["usage"]["output_tokens"],
               "end_reason": ro["end_reason"], "errors": len(ro["errors"]),
               "env": LIVE_ENV if live else "portsim", "rep": row["rep"], "attempt": row["attempt"],
               "cost_usd": row["cost_usd"]}
        if live:
            out |= {"watches": len(ro["live"]["watches"]), "confirms": tools.count("confirm_berths"),
                    "excused_cost": g["excused_cost"], "regret": g["regret"],
                    "rolling_cost": self.references[task.task_id]["rolling"]["cost"]}
        return out

    def rollout(self, run_id: str, model: str, task_id: str) -> dict:
        key = (run_id, model, task_id)
        if key not in self.rollouts:
            run = self.runs[run_id]
            row = run.rows[model, task_id]
            record = json.loads((run.dir / row["transcript"]).read_text())
            task = self.pack.get(task_id)
            ro = record | {"run": run_id, "task_id": task_id, "episode_id": row["instance"].rsplit("-", 1)[1],
                           "started": row["started_utc"],
                           "record": {"sweep": run.sweep.name, "rep": row["rep"], "attempt": row["attempt"],
                                      "cost_usd": row["cost_usd"], "instance": row["instance"]}}
            if run.sweep.live:
                ro |= self.live(task, record["messages"])
            elif record["final"]["submitted"]:
                ro["final"] = record["final"] | {"grade": regrade(task, record["final"]["plan"])}
            self.rollouts[key] = ro
        return self.rollouts[key]

    def live(self, task: Task, messages: list[dict]) -> dict:
        week, steps, opened = replay(task, messages)
        ref = self.references[task.task_id]
        g = week.grade
        moves = evaluate(task, week.plan).moves if g["feasible"] else None
        delivered = {"load": lambda e: 0, "trigger": lambda e: opened[e["watch"]], "env": lambda e: len(steps) - 1}
        bulletins = [{"event_id": e["event_id"], "kind": e["kind"], "from": e["name"],
                      "text": week.scheduled[e["event_id"]].text,
                      "event_hour": week.scheduled[e["event_id"]].event_hour, "watch": e["watch"], "hour": e["hour"],
                      "time": label(e["hour"]), "via": e["via"], "step": delivered[e["via"]](e)} for e in week.log]
        return {
            "steps": steps, "reward": g["reward"],
            "final": {"submitted": week.end_reason == "done", "plan": plan_to_list(week.plan),
                      "grade": g | {"naive_cost": ref["naive"]["cost"], "moves": moves,
                                    "delay_cost": g["cost"] - MOVE_PENALTY * moves if g["feasible"] else None,
                                    "parse_problems": []}},
            "live": {"end_reason": week.end_reason,
                     "watches": [{"index": w.index, "hour": w.hour, "time": label(w.hour),
                                  "virtual_time": virtual_time(task, w.hour),
                                  "frozen_before": w.hour + FREEZE_HOURS if w.index else 0} for w in week.watches],
                     "bulletins": bulletins, "frozen": week.frozen, "refusals": week.refusals,
                     "excused": {"problems": week.excused_problems, "cost": week.excused_cost},
                     "audit": week.audit(),
                     "reference": {"optimal_cost": ref["optimal_cost"], "unavoidable_cost": ref["unavoidable_cost"],
                                   "rolling": {k: v for k, v in ref["rolling"].items() if k != "plans"},
                                   "naive": ref["naive"]}},
        }


def regrade(task: Task, plan) -> dict:
    """The final plan graded as submit_plan grades it."""
    try:
        parsed, problems = parse_plan(task, plan)
    except PlanError as e:
        parsed, problems = {}, [str(e)]
    return grade(task, parsed, problems).as_dict()


def replay(task: Task, messages: list[dict]) -> tuple[Week, list[dict], dict[int, int]]:
    """The recorded calls to the env's tools played back on a Week, each output checked against the recording, then
    the rest of the week run as end_week runs it. Returns the week, a step per planning call and advance, and the step
    that opened each watch."""
    week, steps, opened, calls, turn = Week(task), [], {}, {}, 0
    for m in messages:
        if m["role"] == "assistant":
            turn += 1
            calls |= {c["id"]: (turn, c) for c in m.get("tool_calls") or []}
        elif m["role"] == "tool":
            at, call = calls[m["tool_call_id"]]
            if call["name"] not in TOOLS or week.done or not isinstance(args := _parsed(call["arguments"]), dict):
                continue
            result, plan = play(week, call["name"], args)
            if _json(result) != m["content"]:
                raise ReplayError(f"{call['name']} {call['id']} returned {_json(result)}, recorded {m['content']}")
            if call["name"] == "advance" and not week.done:
                opened[week.watch] = len(steps)
                for n in week.watches[week.watch].notices:
                    week.notice(n.event_id, n.name, n.text, "trigger")
            if call["name"] in STEPS:
                steps.append(step(week, at, call, _parsed(args.get("plan")), result, plan))
    if not week.done:
        week.end()
    return week, steps, opened


def _parsed(value):
    """A JSON string as what it encodes; anything else as it is."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    return value


def play(week: Week, name: str, args: dict) -> tuple[dict, Plan]:
    """What the tool returns, as LiveEpisode counts the call, and the plan it is about: the plan checked, else the
    confirmed windows."""
    week.calls += 1
    if name == "get_situation":
        result = week.situation()
    elif name == "advance":
        result = week.finish("done") if week.last else week.open()
    else:
        raw = _raw(ARGS.validate_python(args["plan"]))
        result = week.check(raw) if name == "check_plan" else week.confirm(raw)
        if name == "check_plan" and "error" not in result:
            return {**result, "messages": week.drain()}, week._merge(raw)[1]
    return {**result, "messages": week.drain()}, week.plan


def step(week: Week, turn: int, call: dict, entries, result: dict, plan: Plan) -> dict:
    view = week.view
    ships = charge(evaluate(view, plan), *week.excuses())
    problems = sum(len(charged) for _, charged, _, _ in ships)
    excused = sum(waived for *_, waived in ships)
    if call["name"] == "check_plan" and "ships" in result:
        result = result | {"violations": [{"ship": s["ship"], "problem": p} for s in result["ships"]
                                          for p in s["problems"]]}
    return {"turn": turn, "tool": call["name"], "call_id": call["id"], "entries": entries,
            "plan": plan_to_list(plan), "result": result, "watch": week.watch, "hour": week.hour,
            "time": label(week.hour), "virtual_time": virtual_time(week.task, week.hour),
            "frozen_before": week.before, "windows": week.windows(view), "unconfirmed": week.unconfirmed(view),
            "revealed": list(week.revealed),
            "known": {"feasible": not problems, "problems": problems, "excused_cost": excused,
                      "cost": sum(r.cost for r, *_ in ships) - excused if not problems else None}}
