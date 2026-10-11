"""PortSim lines: the wind week with the shipping lines answering back. Each ship's agent, the firm that deals with
the port for its line, reports the ship's ETA 48 and 24 hours out and calls in an hour before it arrives; the ETAs are
optimistic and firm up as the ship nears. The planner can ask a firm for a ship's ETA and request an arrival time, which
the firm agrees when the ship can make it by slowing down. Ships berth first come, first served: none may start while a
ship earlier in the queue waits at anchor, unless the wind holds that ship; a ship's turn is its arrival at cruising
speed, so a ship slowed on request keeps it. An hour at anchor costs what an hour late does.

``rules["lines"]`` holds each ship's firm, its previous port's distance and its ETA bias; the truth is each ship's
``arrival`` (at cruising speed) and the arrival times agreed during the week."""

import json
import math
import os
from dataclasses import replace
from importlib.resources import files
from pathlib import Path

from berth_core import Plan, Task, TaskPack
from berth_core.check import PlanResult
from berth_core.model import MOVE_PENALTY

from . import marine, wind, world
from .schedule import LINES_PACK, Notice, Watch, label
from .schedule import schedule as v4_schedule
from .wind import WindWeek

CRUISE_KN = 17
SLOWEST_KN = 10
STRETCH = CRUISE_KN / SLOWEST_KN
REPORT_LEADS = (48, 24)
CALL_LEAD = 1
ETA_ERROR = 0.2
SPEAKER = "Ship's agent"
REPORTS = ("eta", "call")
NEWS_ETA = ("late", "bunching", "extra")
REFERENCES = files("agentenv_portsim") / "data" / "lines" / "references.jsonl"


def pack_dir() -> Path:
    """Beside the first BERTH_TASKS_DIR pack when that is set (the env image), else in the package's data."""
    if roots := os.environ.get("BERTH_TASKS_DIR"):
        return Path(roots.split(":")[0]).parent / LINES_PACK
    return files("agentenv_portsim") / "data" / LINES_PACK


def pack() -> TaskPack:
    return TaskPack(pack_dir())


def references() -> list[dict]:
    return [json.loads(line) for line in REFERENCES.read_text().splitlines()]


def task_ids() -> list[str]:
    return [r["task_id"] for r in references() if r["qualifies"]]


def meta(task: Task, sid: int) -> dict:
    return task.rules["lines"]["ships"][sid]


def firm(task: Task, sid: int) -> str:
    return meta(task, sid)["firm"]


def firm_name(task: Task, firm_id: str) -> str:
    return task.rules["lines"]["firms"][firm_id]


def leg_hours(task: Task, sid: int) -> float | None:
    nm = meta(task, sid)["leg_nm"]
    return None if nm is None else nm / CRUISE_KN


def departure(task: Task, sid: int) -> float | None:
    """The hour the ship leaves its previous port, sailing at cruising speed; None when that is beyond the week's
    reach."""
    leg = leg_hours(task, sid)
    return None if leg is None else task.ships[sid].arrival - leg


def estimate(task: Task, sid: int, hour: int) -> int:
    """The firm's ETA for an unslowed ship at ``hour``: off by a share of the hours left, mostly early (the ship arrives
    later), exact from the arrival call."""
    a = task.ships[sid].arrival
    if a - hour <= CALL_LEAD:
        return a
    return max(hour + 1, a - round(ETA_ERROR * meta(task, sid)["bias"] * (a - hour)))


def first_known(task: Task) -> dict[int, int]:
    """The hour a ship's own news first reaches the planner, for the ships whose arrival v4 announced: an unscheduled
    call when its notice reveals it, a late or bunched ship when the notice about it comes. Their agents' reports start
    after it, so no report gives the news away early."""
    out = {}
    for w in v4_schedule(task):
        for n in w.notices:
            if n.kind in NEWS_ETA:
                for s in [n.event["ship"]] if n.kind != "bunching" else n.event["ships"]:
                    out[s] = max(out.get(s, n.hour), n.hour)
    return out


def timetable(task: Task) -> list[Watch]:
    """v4's watches, unchanged, each also carrying the ETA reports and arrival calls made since the watch before:
    routine reports add no watch, so they wait for the next bulletin, and the latest one made before hour 0 opens the
    week."""
    watches = v4_schedule(task)
    hours = [w.hour for w in watches]
    news = first_known(task)
    reports: dict[int, list[Notice]] = {k: [] for k in range(len(watches))}
    for s in task.ships:
        made = [(s.arrival - lead, "eta", lead) for lead in REPORT_LEADS] + [(s.arrival - CALL_LEAD, "call", CALL_LEAD)]
        if s.id in news:
            made = [m for m in made if m[0] > news[s.id]]
        else:
            before = [m for m in made if m[0] <= 0]
            made = [m for m in made if m[0] > 0] + ([max(before)] if before else [])
        for hour, kind, lead in made:
            k = next((k for k, h in enumerate(hours) if h >= hour), None)
            if k is None:
                continue
            at = max(hour, 0)
            event = {"type": kind, "ship": s.id, "hour": at, "lead": lead,
                     "eta": s.arrival if kind == "call" else estimate(task, s.id, at)}
            reports[k].append(Notice(f"{kind}-{s.id}-{lead}", -1, kind, firm_name(task, firm(task, s.id)), at,
                                     s.arrival, report_text(task, event), event))
    return [Watch(w.index, w.hour, w.notices + tuple(sorted(reports[w.index], key=lambda n: (n.hour, n.event_id))))
            for w in watches]


def report_text(task: Task, event: dict) -> str:
    s = task.ships[event["ship"]]
    if event["type"] == "call":
        return f"{s.name} (ship {s.id}) calls in: at buoy S, arriving hour {event['eta']} ({label(event['eta'])})."
    return (f"{s.name} (ship {s.id}): ETA {label(event['eta'])} (hour {event['eta']}), as of "
            f"{label(event['hour'])}.")


def _queued(task: Task, plan: Plan, res: PlanResult) -> None:
    """Each ship that starts berthing while a ship earlier in the queue waits at anchor, unheld by the wind, breaks
    the queue rule; the first such ship is named."""
    turns = task.rules["lines"]["turns"]
    starts = {r.ship: r.berth_hour for r in res.ships if r.berth_hour is not None}
    for y, ty in sorted(starts.items()):
        for x in sorted(starts, key=lambda x: (turns[x], x)):
            if turns[x] >= turns[y]:
                break
            if task.ships[x].arrival <= ty < starts[x] and not any(
                    a <= ty < b for a, b in task.no_move_windows(task.ships[x])):
                res.ships[y].problems.append(f"berths at hour {ty} while ship {x} {task.ships[x].name}, earlier in "
                                             f"the queue, waits at anchor")
                break


def evaluate(task: Task, plan: Plan) -> PlanResult:
    """marine.evaluate with the queue rule, and each hour a ship waits at anchor charged as an hour late is: its
    sections times the hours between its arrival and its berthing."""
    res = marine.evaluate(task, plan)
    for r in res.ships:
        arrival = task.ships[r.ship].arrival
        if r.berth_hour is not None and r.berth_hour > arrival:
            r.cost += task.ships[r.ship].sections * (r.berth_hour - arrival)
    _queued(task, plan, res)
    if any(r.problems for r in res.ships):
        return PlanResult(False, res.ships, None, None, None)
    cost = sum(r.cost for r in res.ships)
    moves = sum(r.moved for r in res.ships)
    return PlanResult(True, res.ships, cost, cost - MOVE_PENALTY * moves, moves)


def anchor_hours(task: Task, res: PlanResult) -> int:
    return sum(r.berth_hour - task.ships[r.ship].arrival for r in res.ships
               if r.berth_hour is not None and r.berth_hour > task.ships[r.ship].arrival)


def with_arrivals(task: Task, arrivals: dict[int, int], turns: dict[int, int]) -> Task:
    ships = [replace(s, arrival=arrivals[s.id]) for s in task.ships]
    return replace(task, ships=ships, rules=task.rules | {"lines": task.rules["lines"] | {
        "turns": [turns[s.id] for s in task.ships]}})


class LinesWeek(WindWeek):
    timetable = staticmethod(timetable)
    evaluate = staticmethod(evaluate)
    untimed = REPORTS

    def __init__(self, task: Task):
        self.locks: dict[int, tuple[float, float, int]] = {}
        self.told: dict[int, tuple[int, int]] = {}
        self.arrived: set[int] = set()
        self.exchanges: list[dict] = []
        super().__init__(task)

    def notice(self, event_id: str, name: str, text: str, via: str) -> dict:
        out = super().notice(event_id, name, text, via)
        event = self.scheduled[event_id].event
        if event["type"] in REPORTS:
            self._tell(event["ship"], event["hour"], event["eta"])
            if event["type"] == "call":
                self.arrived.add(event["ship"])
        elif event["type"] in ("late", "extra"):
            self._tell(event["ship"], self.hour, event["eta"])
        elif event["type"] == "bunching":
            for s, eta in zip(event["ships"], event["etas"], strict=True):
                self._tell(s, self.hour, eta)
        return out

    def _tell(self, sid: int, as_of: int, eta: int) -> None:
        if sid not in self.locks and (sid not in self.told or self.told[sid][0] <= as_of):
            self.told[sid] = (as_of, eta)

    def actual(self, sid: int) -> int:
        """When the ship really arrives: at the agreed time, else at cruising speed."""
        return self.locks[sid][2] if sid in self.locks else self.task.ships[sid].arrival

    def turn(self, sid: int) -> int:
        return self.task.ships[sid].arrival

    def known_arrival(self, view: Task, sid: int) -> int:
        if sid in self.locks or sid in self.arrived:
            return self.actual(sid)
        return self.told[sid][1] if sid in self.told else view.ships[sid].arrival

    def known_turn(self, view: Task, sid: int) -> int:
        return self.turn(sid) if sid in self.locks or sid in self.arrived else self.known_arrival(view, sid)

    @property
    def view(self) -> Task:
        view = wind.known(self.task, self.revealed)
        visible = {s.id for s in view.ships}
        return with_arrivals(view, {s: self.known_arrival(view, s) for s in visible},
                             {s: self.known_turn(view, s) for s in visible})

    def truth(self) -> Task:
        ids = range(len(self.task.ships))
        return with_arrivals(self.task, {s: self.actual(s) for s in ids}, {s: self.turn(s) for s in ids})

    def past(self, revealed: list[str], target: Task) -> Task:
        """The week as known then, with the target's arrivals and turns: an ETA that proved wrong is no news, so the
        excuses never waive it."""
        view = wind.known(self.task, revealed)
        arrivals = {s.id: s.arrival for s in target.ships}
        turns = dict(zip(arrivals, target.rules["lines"]["turns"], strict=True))
        return with_arrivals(view, {s.id: arrivals[s.id] for s in view.ships}, {s.id: turns[s.id] for s in view.ships})

    def target(self) -> Task:
        return self.truth() if self.done else self.view

    def finish(self, end_reason: str) -> dict:
        self.done, self.end_reason = True, end_reason
        truth = self.truth()
        unslowed = with_arrivals(self.task, {s.id: s.arrival for s in self.task.ships},
                                 {s.id: s.arrival for s in self.task.ships})
        self.grade = world.grade_week(unslowed, self.plan, *self.excuses(),
                                      evaluate=lambda _task, plan: evaluate(truth, plan))
        self.grade["anchor_hours"] = anchor_hours(truth, evaluate(truth, self.plan))
        return {"done": True, "feasible": self.grade["feasible"], "cost": self.grade["cost"],
                "reward": self.grade["reward"]}

    def situation(self) -> dict:
        out = super().situation()
        return out | {"situation": out["situation"] + "\n\n" + section(self)}

    def remaining(self, sid: int, hour: int) -> tuple[float, float]:
        """(the hour from which the ship can change pace, the hours it still needs at cruising speed then)."""
        dep = departure(self.task, sid)
        start = hour if dep is None else max(hour, dep)
        if sid in self.locks:
            ref, left, at = self.locks[sid]
            start = max(start, ref)
            return start, left * (at - start) / (at - ref) if at > ref else 0.0
        return start, self.task.ships[sid].arrival - start

    def reach(self, sid: int, hour: int) -> tuple[int, int]:
        """The earliest and latest hours the ship can arrive, from ``hour`` on."""
        start, left = self.remaining(sid, hour)
        return math.ceil(start + left - 1e-9), math.floor(start + left * STRETCH + 1e-9)

    def _ship(self, firm_id: str, sid) -> int:
        view = self.view
        if not isinstance(sid, int) or isinstance(sid, bool) or sid not in {s.id for s in view.ships}:
            raise ValueError(f"no ship {sid!r} in the week")
        if firm(self.task, sid) != firm_id:
            raise ValueError(f"ship {sid} {self.task.ships[sid].name} is not this agent's: "
                             f"{firm_name(self.task, firm(self.task, sid))} handles it")
        return sid

    def status(self, firm_id: str, sid) -> dict:
        sid = self._ship(firm_id, sid)
        name, hour = self.task.ships[sid].name, self.hour
        if self.actual(sid) <= hour:
            out = {"ship": sid, "name": name, "arrived": self.actual(sid), "turn": self.turn(sid)}
            self.arrived.add(sid)
        elif sid in self.locks:
            out = {"ship": sid, "name": name, "eta": self.actual(sid), "agreed": True, "turn": self.turn(sid)}
        else:
            eta = estimate(self.task, sid, hour)
            self._tell(sid, hour, eta)
            out = {"ship": sid, "name": name, "eta": eta, "as_of": hour}
        self.exchanges.append({"watch": self.watch, "hour": hour, "firm": firm_id, "ship": sid, "ask": "eta",
                               "call": self.calls, "reply": out})
        return out

    def request(self, firm_id: str, sid, arrival) -> dict:
        sid = self._ship(firm_id, sid)
        if not isinstance(arrival, int) or isinstance(arrival, bool):
            raise ValueError(f"request_arrival must be an hour, got {arrival!r}")
        name, hour = self.task.ships[sid].name, self.hour
        if self.actual(sid) <= hour:
            out = {"ship": sid, "name": name, "agreed": False, "reason": f"already arrived at hour {self.actual(sid)}"}
        else:
            earliest, latest = self.reach(sid, hour)
            if earliest <= arrival <= latest:
                self.locks[sid] = (*self.remaining(sid, hour), arrival)
                self.told[sid] = (hour, arrival)
                out = {"ship": sid, "name": name, "agreed": True, "arrival": arrival, "turn": self.turn(sid),
                       "slowing": arrival > earliest}
            else:
                eta = self.actual(sid) if sid in self.locks else estimate(self.task, sid, hour)
                out = {"ship": sid, "name": name, "agreed": False, "eta": eta, "reason": (
                    "can't arrive that early" if arrival < earliest else "can't slow down that much")}
        self.exchanges.append({"watch": self.watch, "hour": hour, "firm": firm_id, "ship": sid,
                               "ask": "request_arrival", "arrival": arrival, "call": self.calls, "reply": out})
        return out

    def audit(self) -> dict:
        out = super().audit()
        problems = list(out["problems"])
        truth = self.truth()
        for sid, (_, _, at) in self.locks.items():
            if truth.ships[sid].arrival != at:
                problems.append(f"ship {sid} agreed hour {at} but arrives at {truth.ships[sid].arrival}")
        return {"ok": not problems, "problems": problems}

    def data(self) -> dict:
        return super().data() | {
            "lines": {"exchanges": self.exchanges,
                      "agreed": [{"ship": s, "arrival": at, "turn": self.turn(s)} for s, (_, _, at) in
                                 sorted(self.locks.items())],
                      "arrivals": [{"ship": s.id, "arrival": self.actual(s.id), "turn": self.turn(s.id)}
                                   for s in self.task.ships] if self.done else []}}


def firms_in(view: Task) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for s in view.ships:
        out.setdefault(firm(view, s.id), []).append(s.id)
    return out


def section(week: LinesWeek) -> str:
    view = week.view
    lines = [
        "## Arrivals and the ships' agents",
        "- Each ship's agent reports its ETA 48 and 24 hours out, and the ship calls in an hour before it arrives; "
        "reports made between watches arrive with the next one. ETAs are optimistic: most ships arrive later than their "
        "agent says, by less as they near.",
        "- Message a ship's agent to ask for its ETA or to request an arrival time. The agent agrees when the ship can "
        f"make it at {CRUISE_KN} kn or by slowing to as little as {SLOWEST_KN} kn once it has left its previous port, "
        "and the ship then arrives at that hour.",
        "- Ships berth first come, first served: no ship may start berthing while a ship earlier in the queue waits at "
        "anchor, unless the wind holds that ship. A ship's turn is when it would arrive at cruising speed, so a ship "
        "slowed at your request keeps its turn.",
        "- Each hour a ship waits at anchor between its arrival and its berthing costs its sections, as an hour late "
        "does.",
        "- Agents, and their ships: " + "; ".join(
            f"{firm_name(view, f)} ({f}): ships {', '.join(map(str, ids))}" for f, ids in sorted(firms_in(view).items()))
        + "."]
    rows = []
    for s in view.ships:
        if s.id in week.locks:
            state = f"agreed hour {week.actual(s.id)}, turn {week.turn(s.id)}"
        elif s.id in week.arrived:
            state = f"arrived hour {week.actual(s.id)}, turn {week.turn(s.id)}"
        elif s.id in week.told:
            as_of, eta = week.told[s.id]
            state = f"ETA hour {eta}, as of {label(as_of)}"
        else:
            state = "published schedule"
        rows.append(f"- ship {s.id} {s.name}: arrival hour {s.arrival}, {state}; from {s.from_port or 'unknown'}")
    return "\n".join(lines + ["- Arrivals as known now:"] + rows)


def step_lines(week: LinesWeek) -> dict:
    view = week.view
    return {"agreed": [{"ship": s, "arrival": at} for s, (_, _, at) in sorted(week.locks.items())],
            "arrivals": [{"ship": s.id, "arrival": s.arrival, "known": s.id in week.locks or s.id in week.arrived}
                         for s in view.ships],
            "exchanges": [e for e in week.exchanges if e["watch"] == week.watch]}

