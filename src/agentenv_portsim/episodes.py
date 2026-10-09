"""Recorded sweep runs as the episode summaries and rollouts PortSimEnv's viewer reads: a v1 run regraded from its
final plan, a live run replayed through its Week from the recorded tool calls."""

import json
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import click
from berth_core import MOVE_PENALTY, Plan, PlanError, Task, TaskPack, evaluate, grade, parse_plan, plan_to_list
from pydantic import TypeAdapter

from . import marine, tasks, wind
from .live import WindowsArg, _json, _raw
from .marine import MarineWeek, step_marine
from .schedule import FREEZE_HOURS, LIVE_ENV, MARINE_ENV, TOOLS, WIND_ENV, label, virtual_time
from .sweep import EVAL_PACK, Sweep, results
from .wind import WindWeek, step_wind
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


def env(sweep: Sweep) -> str:
    return WIND_ENV if sweep.wind else MARINE_ENV if sweep.marine else LIVE_ENV if sweep.live else "portsim"


def week_of(sweep: Sweep) -> type[Week]:
    return WindWeek if sweep.wind else MarineWeek if sweep.marine else Week


class Runs:
    """The scored attempt of each model and task in the sweeps under ``root``: one viewer run per sweep and rep."""

    def __init__(self, root: Path, names: list[str] | None = None):
        self.pack = TaskPack(tasks.PACKS / EVAL_PACK)
        self.marine_pack = marine.pack()
        self.references = {r["task_id"]: r for r in tasks.live_references()}
        self.marine_references = {r["task_id"]: r for r in marine.references()}
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
        self.wind_tasks = {t for run in self.runs.values() if run.sweep.wind for t in run.sweep.tasks}

    @cached_property
    def wind_pack(self) -> TaskPack:
        return wind.pack()

    @cached_property
    def wind_references(self) -> dict[str, dict]:
        return {r["task_id"]: r for r in wind.references()}

    def has(self, task_id: str) -> bool:
        """A week the explorer serves: dock-v1-eval's, whose ids the marine pack shares, or a wind sweep's."""
        return task_id in self.pack._by_id or task_id in self.wind_tasks

    def tasks(self) -> list[dict]:
        ids = sorted({task_id for run in self.runs.values() for _, task_id in run.rows})
        return [{"task_id": t.task_id, "split": t.split, "quay": t.quay, "terminal": t.terminal, "week": t.week,
                 "difficulty": t.difficulty, "ships": len(t.ships), "disruptions": [e["type"] for e in t.disruptions]}
                for t in map(self.task, ids)]

    def task(self, task_id: str) -> Task:
        """The explorer's week: a wind sweep's from the wind pack; else the marine one when every run of the task is
        marine, else dock-v1-eval's, the two packs sharing task ids."""
        if task_id in self.wind_tasks:
            return self.wind_pack.get(task_id)
        marine_runs = [run.sweep.marine for run in self.runs.values() if any(t == task_id for _, t in run.rows)]
        return (self.marine_pack if marine_runs and all(marine_runs) else self.pack).get(task_id)

    def pack_of(self, run: Run) -> TaskPack:
        return self.wind_pack if run.sweep.wind else self.marine_pack if run.sweep.marine else self.pack

    def references_of(self, week: type[Week]) -> dict[str, dict]:
        return (self.wind_references if issubclass(week, WindWeek) else self.marine_references
                if issubclass(week, MarineWeek) else self.references)

    def index(self) -> list[dict]:
        out = []
        for run_id, run in sorted(self.runs.items()):
            episodes, failed = self.replayed(run_id)
            if episodes or failed:
                out.append({"run": run_id, "models": sorted({e["model"] for e in episodes + failed}),
                            "episodes": len(episodes),
                            "mean_reward": round(sum(e["reward"] for e in episodes) / len(episodes), 4)
                            if episodes else None,
                            "env": env(run.sweep), "sweep": run.sweep.name, "rep": run.rep,
                            "k": run.sweep.k, "episode_cap_usd": run.sweep.episode_cap_usd, "failed": failed})
        return out

    def episodes(self, run_id: str) -> list[dict]:
        return self.replayed(run_id)[0]

    def replayed(self, run_id: str) -> tuple[list[dict], list[dict]]:
        """The summaries of the run's episodes that replay, and the error of each that doesn't: a recording made
        before the week changed."""
        run, out, failed = self.runs[run_id], [], []
        for model, task_id in sorted(run.rows):
            try:
                out.append(self.summary(run, run.rows[model, task_id]))
            except ReplayError as e:
                failed.append({"model": model, "task_id": task_id, "error": str(e)})
        return out, failed

    def summary(self, run: Run, row: dict) -> dict:
        """upstream's summarize() (eval/run_eval.py), and the attempt's record; a live run's week too."""
        ro = self.rollout(run.id, row["model"], row["task_id"])
        task = self.pack_of(run).get(row["task_id"])
        refs = self.references_of(week_of(run.sweep))
        g = ro["final"].get("grade") or {}
        tools = [s["tool"] for s in ro["steps"]]
        live = run.sweep.live
        out = {"model": row["model"], "task_id": task.task_id, "split": task.split, "difficulty": task.difficulty,
               "quay": task.quay, "ships": len(task.ships), "reward": ro["reward"],
               "submitted": bool(ro["final"]["submitted"]), "feasible": bool(g.get("feasible")), "cost": g.get("cost"),
               "optimal_cost": task.reference["optimal_cost"],
               "naive_cost": refs[task.task_id]["naive"]["cost"] if live else task.reference["naive_cost"],
               "turns": ro["turns"], "checks": tools.count("check_plan"), "seconds": ro["seconds"],
               "input_tokens": ro["usage"]["input_tokens"], "output_tokens": ro["usage"]["output_tokens"],
               "end_reason": ro["end_reason"], "errors": len(ro["errors"]),
               "env": env(run.sweep), "rep": row["rep"], "attempt": row["attempt"],
               "cost_usd": row["cost_usd"]}
        if live:
            out |= {"watches": len(ro["live"]["watches"]), "confirms": tools.count("confirm_berths"),
                    "excused_cost": g["excused_cost"], "regret": g["regret"],
                    "rolling_cost": refs[task.task_id]["rolling"]["cost"]}
        if run.sweep.wind:
            out |= {"weather": refs[task.task_id]["weather"], "hindsight_cost": refs[task.task_id]["hindsight_cost"]}
        return out

    def rollout(self, run_id: str, model: str, task_id: str) -> dict:
        key = (run_id, model, task_id)
        if key not in self.rollouts:
            run = self.runs[run_id]
            row = run.rows[model, task_id]
            record = json.loads((run.dir / row["transcript"]).read_text())
            task = self.pack_of(run).get(task_id)
            ro = record | {"run": run_id, "task_id": task_id, "episode_id": row["instance"].rsplit("-", 1)[1],
                           "started": row["started_utc"],
                           "record": {"sweep": run.sweep.name, "rep": row["rep"], "attempt": row["attempt"],
                                      "cost_usd": row["cost_usd"], "instance": row["instance"]}}
            if run.sweep.live:
                ro |= self.live(task, record["messages"], week_of(run.sweep))
            elif record["final"]["submitted"]:
                ro["final"] = record["final"] | {"grade": regrade(task, record["final"]["plan"])}
            self.rollouts[key] = ro
        return self.rollouts[key]

    def live(self, task: Task, messages: list[dict], week: type[Week] = Week) -> dict:
        ref = self.references_of(week)[task.task_id]
        week, steps, opened = replay(task, messages, week)
        g = week.grade
        moves = sum(r.moved for r in evaluate(task, week.plan).ships) if g["feasible"] else None
        delivered = {"load": lambda e: 0, "trigger": lambda e: opened[e["watch"]], "env": lambda e: len(steps) - 1}
        bulletins = [{"event_id": e["event_id"], "kind": e["kind"], "from": e["name"],
                      "text": week.scheduled[e["event_id"]].text,
                      "event_hour": week.scheduled[e["event_id"]].event_hour, "watch": e["watch"], "hour": e["hour"],
                      "time": label(e["hour"]), "via": e["via"], "step": delivered[e["via"]](e)} for e in week.log]
        reference = {"optimal_cost": ref["optimal_cost"], "unavoidable_cost": ref["unavoidable_cost"],
                     "rolling": _played(ref["rolling"]), "naive": ref["naive"]}
        if isinstance(week, WindWeek):
            reference |= {"hindsight_cost": ref["hindsight_cost"]} | {
                mode: _played(ref[mode]) for mode in ("blind", "hold") if mode in ref}
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
                     "audit": week.audit(), "reference": reference},
        }


def _played(policy: dict) -> dict:
    """A reference policy's outcome, without its plans and configurations."""
    return {k: v for k, v in policy.items() if k not in ("plans", "configs")}


def regrade(task: Task, plan) -> dict:
    """The final plan graded as submit_plan grades it."""
    try:
        parsed, problems = parse_plan(task, plan)
    except PlanError as e:
        parsed, problems = {}, [str(e)]
    return grade(task, parsed, problems).as_dict()


def replay(task: Task, messages: list[dict], week: type[Week] = Week) -> tuple[Week, list[dict], dict[int, int]]:
    """The recorded calls to the env's tools played back on a Week, each output checked against the recording, then
    the rest of the week run as end_week runs it. Returns the week, a step per planning call and advance, and the step
    that opened each watch."""
    week, steps, opened, calls, turn = week(task), [], {}, {}, 0
    for m in messages:
        if m["role"] == "assistant":
            turn += 1
            calls |= {c["id"]: (turn, c) for c in m.get("tool_calls") or []}
        elif m["role"] == "tool":
            at, call = calls[m["tool_call_id"]]
            if call["name"] not in TOOLS or week.done or not isinstance(args := _parsed(call["arguments"]), dict):
                continue
            if call["name"] in ("check_plan", "confirm_berths") and "plan" not in args:
                continue  # the tool's input schema refused it before the week saw it
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
    ships = charge(week.evaluate(view, plan), *week.excuses())
    problems = sum(len(charged) for _, charged, _, _ in ships)
    excused = sum(waived for *_, waived in ships)
    if call["name"] == "check_plan" and "ships" in result:
        result = result | {"violations": [{"ship": s["ship"], "problem": p} for s in result["ships"]
                                          for p in s["problems"]]}
    return {"turn": turn, "tool": call["name"], "call_id": call["id"], "entries": entries,
            "plan": plan_to_list(plan), "result": result, "watch": week.watch, "hour": week.hour,
            "time": label(week.hour), "virtual_time": virtual_time(week.task, week.hour),
            "frozen_before": week.before, "windows": week.windows(view), "unconfirmed": week.unconfirmed(view),
            "revealed": list(week.revealed), "task": view.to_dict(public=True),
            "known": {"feasible": not problems, "problems": problems, "excused_cost": excused,
                      "cost": sum(r.cost for r, *_ in ships) - excused if not problems else None}} | (
        {"marine": step_marine(view, plan)} if isinstance(week, MarineWeek) else {}) | (
        {"wind": step_wind(view)} if isinstance(week, WindWeek) else {})
