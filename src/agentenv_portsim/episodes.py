"""Recorded sweep runs as the episode summaries and rollouts PortSimEnv's viewer reads: a v1 run regraded from its
final plan, a live run replayed through its Week from the recorded tool calls; a lines run also from the planner's
messages to the ships' agents, each played on the week as the agent asks the env."""

import json
import threading
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property
from importlib.metadata import version
from pathlib import Path
from typing import Any, TypeVar

import click
from berth_core import MOVE_PENALTY, Plan, PlanError, Task, TaskPack, evaluate, grade, parse_plan, plan_to_list
from pydantic import TypeAdapter, ValidationError

from . import lines, marine, tasks, wind
from .lines import LinesWeek, step_lines
from .live import WindowsArg, _json, _raw
from .marine import MarineWeek, step_marine
from .schedule import FREEZE_HOURS, LINES_ENV, LIVE_ENV, MARINE_ENV, TOOLS, WIND_ENV, label, virtual_time
from .sweep import EVAL_PACK, Sweep, results
from .wind import WindWeek, step_wind
from .world import Week, charge

ARGS = TypeAdapter(WindowsArg)
INT = TypeAdapter(int)
STEPS = ("check_plan", "confirm_berths", "advance")
MESSAGE_TOOL = "message_agent"
MAX_REQUESTS = 20
"""portsim-line's cap on the requests in one message."""
V = TypeVar("V")
SUMMARIES = "summaries.json"
"""Beside a published sweep: its runs' episode summaries as the dataset build replayed them, under the plugin version
that built it ({"plugin": ..., "runs": Runs.summaries(sweep)}), which a viewer of that version lists without
replaying."""


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
    return (LINES_ENV if sweep.lines else WIND_ENV if sweep.wind else MARINE_ENV if sweep.marine
            else LIVE_ENV if sweep.live else "portsim")


def week_of(sweep: Sweep) -> type[Week]:
    return LinesWeek if sweep.lines else WindWeek if sweep.wind else MarineWeek if sweep.marine else Week


class Runs:
    """The scored attempt of each model and task in the sweeps under ``root``: one viewer run per sweep and rep."""

    def __init__(self, root: Path, names: list[str] | None = None):
        self.pack = TaskPack(tasks.PACKS / EVAL_PACK)
        self.marine_pack = marine.pack()
        self.references = {r["task_id"]: r for r in tasks.live_references()}
        self.marine_references = {r["task_id"]: r for r in marine.references()}
        self.runs: dict[str, Run] = {}
        self.rollouts: dict[tuple[str, str, str], dict] = {}
        self.replays: dict[str, tuple[list[dict], list[dict]]] = {}
        self.locks: dict[object, threading.Lock] = {}
        self.guard = threading.Lock()
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
            stored = root / name / SUMMARIES
            if stored.is_file() and (data := json.loads(stored.read_text()))["plugin"] == version("agentenv-portsim"):
                self.replays |= {run_id: (r["episodes"], r["failed"]) for run_id, r in data["runs"].items()}
        self.wind_tasks = {t for run in self.runs.values() if run.sweep.wind for t in run.sweep.tasks}
        self.lines_tasks = {t for run in self.runs.values() if run.sweep.lines for t in run.sweep.tasks}

    @cached_property
    def wind_pack(self) -> TaskPack:
        return wind.pack()

    @cached_property
    def wind_references(self) -> dict[str, dict]:
        return {r["task_id"]: r for r in wind.references()}

    @cached_property
    def lines_pack(self) -> TaskPack:
        return lines.pack()

    @cached_property
    def lines_references(self) -> dict[str, dict]:
        return {r["task_id"]: r for r in lines.references()}

    def has(self, task_id: str) -> bool:
        """A week the explorer serves: dock-v1-eval's, whose ids the marine pack shares, or a wind or lines sweep's."""
        return task_id in self.pack._by_id or task_id in self.wind_tasks or task_id in self.lines_tasks

    def tasks(self) -> list[dict]:
        ids = sorted({task_id for run in self.runs.values() for _, task_id in run.rows})
        return [{"task_id": t.task_id, "split": t.split, "quay": t.quay, "terminal": t.terminal, "week": t.week,
                 "difficulty": t.difficulty, "ships": len(t.ships), "disruptions": [e["type"] for e in t.disruptions]}
                for t in map(self.task, ids)]

    def task(self, task_id: str) -> Task:
        """The explorer's week: a wind sweep's from the wind pack, else a lines sweep's from the lines pack, the two
        sharing task ids; else the marine one when every run of the task is marine, else dock-v1-eval's, the two packs
        sharing task ids."""
        if task_id in self.wind_tasks:
            return self.wind_pack.get(task_id)
        if task_id in self.lines_tasks:
            return self.lines_pack.get(task_id)
        marine_runs = [run.sweep.marine for run in self.runs.values() if any(t == task_id for _, t in run.rows)]
        return (self.marine_pack if marine_runs and all(marine_runs) else self.pack).get(task_id)

    def pack_of(self, run: Run) -> TaskPack:
        return (self.lines_pack if run.sweep.lines else self.wind_pack if run.sweep.wind
                else self.marine_pack if run.sweep.marine else self.pack)

    def references_of(self, week: type[Week]) -> dict[str, dict]:
        return (self.lines_references if issubclass(week, LinesWeek) else self.wind_references
                if issubclass(week, WindWeek) else self.marine_references if issubclass(week, MarineWeek)
                else self.references)

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

    def summaries(self, name: str) -> dict[str, dict]:
        """The episodes and failures of each run of the sweep ``name``, as SUMMARIES holds them."""
        replayed = {run_id: self.replayed(run_id) for run_id, run in self.runs.items() if run.sweep.name == name}
        return {run_id: {"episodes": episodes, "failed": failed} for run_id, (episodes, failed) in replayed.items()}

    def replayed(self, run_id: str) -> tuple[list[dict], list[dict]]:
        """The summaries of the run's episodes that replay, and the error of each that doesn't: a recording made
        before the week changed."""
        return self.once(self.replays, run_id, lambda: self.replay(run_id))

    def replay(self, run_id: str) -> tuple[list[dict], list[dict]]:
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
        if run.sweep.lines:
            ref = refs[task.task_id]
            out |= {"weather": task.task_id.rsplit("-", 1)[1], "hindsight_cost": ref["hindsight_cost"],
                    "silent_cost": ref["silent"]["cost"], "anchor_hours": g["anchor_hours"],
                    "messages": len(ro["live"]["lines"]["exchanges"])}
        return out

    def rollout(self, run_id: str, model: str, task_id: str) -> dict:
        return self.once(self.rollouts, (run_id, model, task_id), lambda: self.played(run_id, model, task_id))

    def once(self, cache: dict[Any, V], key: object, compute: Callable[[], V]) -> V:
        """``cache[key]``, computed by the first caller while the others wait for it: the viewer's requests come in
        parallel, and replaying a lines week takes seconds."""
        if key not in cache:
            with self.guard:
                lock = self.locks.setdefault(key, threading.Lock())
            with lock:
                if key not in cache:
                    cache[key] = compute()
        return cache[key]

    def played(self, run_id: str, model: str, task_id: str) -> dict:
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
        return ro

    def live(self, task: Task, messages: list[dict], week: type[Week] = Week) -> dict:
        ref = self.references_of(week)[task.task_id]
        week, steps, opened = replay(task, messages, week)
        g = week.grade
        moves = sum(r.moved for r in evaluate(task, week.plan).ships) if g["feasible"] else None
        delivered = {"load": lambda e: 0, "trigger": lambda e: opened[e["watch"]], "env": lambda e: len(steps) - 1}
        bulletins = [{"event_id": e["event_id"], "kind": e["kind"], "from": e["name"],
                      "text": e.get("text", week.scheduled[e["event_id"]].text),
                      "event_hour": week.scheduled[e["event_id"]].event_hour, "watch": e["watch"], "hour": e["hour"],
                      "time": label(e["hour"]), "via": e["via"], "step": delivered[e["via"]](e)}
                     for e in week.log if e.get("text", "") is not None]
        reference = {"optimal_cost": ref["optimal_cost"], "unavoidable_cost": ref["unavoidable_cost"],
                     "rolling": _played(ref["rolling"]), "naive": ref["naive"]}
        if isinstance(week, WindWeek):
            reference |= {"hindsight_cost": ref["hindsight_cost"]} | {
                mode: _played(ref[mode]) for mode in ("blind", "hold", "silent") if mode in ref}
        out = {
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
        if isinstance(week, LinesWeek):
            out["live"]["lines"] = {"firms": task.rules["lines"]["firms"], "exchanges": week.exchanges}
        return out


def _played(policy: dict) -> dict:
    """A reference policy's outcome, without its plans, configurations and messages."""
    return {k: v for k, v in policy.items() if k not in ("plans", "configs", "exchanges")}


def regrade(task: Task, plan) -> dict:
    """The final plan graded as submit_plan grades it."""
    try:
        parsed, problems = parse_plan(task, plan)
    except PlanError as e:
        parsed, problems = {}, [str(e)]
    return grade(task, parsed, problems).as_dict()


def replay(task: Task, messages: list[dict], week: type[Week] = Week) -> tuple[Week, list[dict], dict[int, int]]:
    """The recorded calls to the env's tools played back on a Week, each output checked against the recording, then
    the rest of the week run as end_week runs it; on a LinesWeek, the planner's messages to the ships' agents too, in
    their place among the calls. Returns the week, a step per planning call, advance and message that reached the env,
    and the step that opened each watch."""
    week, steps, opened, calls, turn = week(task), [], {}, {}, 0
    for m in messages:
        if m["role"] == "assistant":
            turn += 1
            calls |= {c["id"]: (turn, c) for c in m.get("tool_calls") or []}
        elif m["role"] == "tool":
            at, call = calls[m["tool_call_id"]]
            if call["name"] == MESSAGE_TOOL and isinstance(week, LinesWeek) and not week.done:
                if sent := sent_to_agent(week, call, m["content"]):
                    steps.append(step(week, at, call, sent["requests"], _parsed(m["content"]), week.plan))
                continue
            if call["name"] not in TOOLS or week.done or not isinstance(args := _parsed(call["arguments"]), dict):
                continue
            if call["name"] in ("check_plan", "confirm_berths") and not _plan_valid(args):
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


def _plan_valid(args: dict) -> bool:
    try:
        ARGS.validate_python(args["plan"])
    except (KeyError, ValidationError):
        return False
    return True


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


def sent_to_agent(week: LinesWeek, call: dict, content: str) -> dict | None:
    """The message_agent call's arguments once its requests are played on the week, each reply checked against the
    recorded one; None when the message never reached the env: the harness refused it, or the agent didn't answer.
    No replies to requests the agent had to answer is the agent failing after it asked the env (it words its answer
    once every request is answered), so the week keeps them unchecked."""
    recorded = _parsed(content)
    if not isinstance(recorded, dict) or not isinstance(recorded.get("replies"), list):
        return None
    args = _parsed(call["arguments"])
    replies = answers(week, args) if isinstance(args, dict) else None
    if replies is None or recorded["replies"] and [_shape(r) for r in replies] != [
            _shape(r) for r in recorded["replies"]]:
        raise ReplayError(f"{MESSAGE_TOOL} {call['id']} got {_json(replies)}, recorded {_json(recorded['replies'])}")
    return args


def answers(week: LinesWeek, args: dict) -> list[dict] | None:
    """What the ship's agent (portsim-line) replies to the planner's message: each request asked of the env under its
    role, as ship_status or agree_arrival; None when the planner's harness refuses the message before sending it."""
    agent, requests = args.get("agent"), args.get("requests")
    if agent not in week.task.rules["lines"]["firms"] or not isinstance(requests, list) or not requests:
        return None
    if len(requests) > MAX_REQUESTS:
        return []
    return [_answer(week, agent, entry) for entry in requests]


def _answer(week: LinesWeek, firm: str, entry) -> dict:
    if not isinstance(entry, dict) or "ship" not in entry:
        return {"error": "each request names a ship"}
    ask, arrival = entry.get("ask"), entry.get("request_arrival")
    if ask == "eta" and arrival is None:
        out = _asked(week.status, firm, entry["ship"])
        return out | ({"agreed_before": True} if out.get("agreed") else {})
    if ask is None and arrival is not None:
        return _asked(week.request, firm, entry["ship"], arrival) | {"asked": arrival}
    return {"ship": entry["ship"], "error": "ask for the ETA or request an arrival, one per request"}


def _asked(tool, firm: str, *args) -> dict:
    """The env tool's answer, its integer arguments validated as the tool's input schema validates them, or the error
    the agent passes on."""
    try:
        return tool(firm, *(INT.validate_python(a) for a in args))
    except ValueError as e:
        return {"error": str(e)}


def _shape(reply) -> object:
    """A reply as replay compares it: an error by its presence alone, its text being the env's or the agent's
    wording."""
    if not isinstance(reply, dict) or "error" not in reply:
        return reply
    return {k: v for k, v in reply.items() if k != "error"} | {"error": True}


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
        {"wind": step_wind(view)} if isinstance(week, WindWeek) else {}) | (
        {"lines": step_lines(week)} if isinstance(week, LinesWeek) else {})
