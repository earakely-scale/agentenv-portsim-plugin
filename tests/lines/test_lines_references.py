"""data/lines/references.jsonl replayed without ortools: the follower's stored plans and requests, the silent follower's
plans and the naive policy reproduce their stored outcomes through the lines week, the follower takes each counter-offer
at once, the pack carries the anchor and the hindsight optimum, which slows a ship from the watch that brings its news,
and a week qualifies by its three clauses."""

from collections import Counter

import pytest
from berth_core import plan_from_list
from berth_core.check import unavoidable_cost
from berth_core.model import MOVE_PENALTY

from agentenv_portsim import lines, marine, wind, world
from agentenv_portsim.lines import LinesWeek

pytestmark = pytest.mark.skipif(not lines.REFERENCES.is_file(), reason="data/lines/references.jsonl is not built yet")

REFERENCES = lines.references() if lines.REFERENCES.is_file() else []
PACK = {t.task_id: t for t in lines.pack().tasks}
WIND = {t.task_id: t for t in wind.pack().tasks}
OUTCOME = ("cost", "reward", "feasible", "excused_cost", "anchor_hours")
REFS = [pytest.param(r, id=r["task_id"]) for r in REFERENCES]


def outcome(week: LinesWeek) -> dict:
    return {key: week.grade[key] for key in OUTCOME}


def replayed(task, stored: dict) -> LinesWeek:
    """The stored run played again: at each watch its requests re-sent to the ships' agents, then its plan."""
    def policy(week: LinesWeek):
        for e in stored["exchanges"]:
            if e["watch"] == week.watch:
                week.request(lines.firm(task, e["ship"]), e["ship"], e["arrival"])
        return plan_from_list(stored["plans"][week.watch])

    return world.play(task, policy, week=LinesWeek)


def test_the_references_are_the_lines_packs_weeks_in_pack_order():
    assert [r["task_id"] for r in REFERENCES] == list(PACK)
    assert len(REFERENCES) == 15


@pytest.mark.parametrize("ref", REFS)
def test_the_record(ref):
    task = PACK[ref["task_id"]]
    assert list(ref) == ["task_id", "watch_hours", "ships", "firms", "optimal_cost", "hindsight_cost",
                         "wind_optimal_cost", "unavoidable_cost", "rolling", "configs", "silent", "naive", "clauses",
                         "qualifies", "solver", "seconds"]
    assert ref["watch_hours"] == [w.hour for w in lines.timetable(task)]
    assert (ref["ships"], ref["firms"]) == (len(task.ships), len(task.rules["lines"]["firms"]))
    assert ref["unavoidable_cost"] == unavoidable_cost(task)
    assert ref["wind_optimal_cost"] == WIND[ref["task_id"]].reference["optimal_cost"]
    assert list(ref["rolling"]) == ["config", *OUTCOME[:4], "anchor_hours", "plans", "exchanges"]
    assert len(ref["rolling"]["plans"]) == len(ref["watch_hours"]) == len(ref["silent"]["plans"])
    assert len(ref["configs"]) == len(ref["silent"]["configs"]) == 4
    assert ref["silent"]["exchanges"] == []


@pytest.mark.parametrize("ref", REFS)
def test_every_stored_follower_run_replays_to_its_outcome_without_a_solver(ref):
    task, stored = PACK[ref["task_id"]], ref["rolling"]
    week = replayed(task, stored)
    assert outcome(week) == {key: stored[key] for key in OUTCOME}
    assert week.refusals == [] and week.audit() == {"ok": True, "problems": []}
    assert [(e["watch"], e["ship"], e["arrival"], e["reply"]["agreed"]) for e in week.exchanges] == [
        (e["watch"], e["ship"], e["arrival"], e["agreed"]) for e in stored["exchanges"]]
    assert week.data()["lines"]["agreed"] == [
        {"ship": s, "arrival": at, "turn": task.ships[s].arrival} for s, (_, _, at) in sorted(week.locks.items())]
    assert stored["config"] == next(k for k, c in enumerate(ref["configs"]) if "error" not in c)
    assert {key: ref["configs"][stored["config"]][key] for key in ("cost", "reward", "anchor_hours")} == {
        key: stored[key] for key in ("cost", "reward", "anchor_hours")}


@pytest.mark.parametrize("ref", REFS)
def test_the_silent_follower_and_the_naive_policy_replay_to_their_outcomes(ref):
    task = PACK[ref["task_id"]]
    silent = replayed(task, ref["silent"])
    assert outcome(silent) == {key: ref["silent"][key] for key in OUTCOME} and silent.exchanges == []
    naive = world.play(task, world.naive, week=LinesWeek)
    assert outcome(naive) == ref["naive"]


@pytest.mark.parametrize("ref", REFS)
def test_the_anchor_is_the_lower_of_the_hindsight_optimum_and_the_followers_best(ref):
    task = PACK[ref["task_id"]]
    costs = [c["cost"] for c in ref["configs"] if c["cost"] is not None]
    assert ref["optimal_cost"] == min([ref["hindsight_cost"], *costs]) == task.reference["optimal_cost"]
    assert ref["hindsight_cost"] == task.reference["lower_bound"]
    assert task.reference["proven_optimal"] is False


def test_every_week_qualifies_and_the_follower_beats_hindsight_only_where_the_news_excuses_more_of_its_cost():
    """The hindsight player slows a ship only from the watch that brings its news; the follower's agreements made
    before it may lapse, and v4's rule lets the news excuse what follows. Asking the agents pays: the follower averages
    0.564, the silent follower 0.107 and the naive policy 0.075."""
    assert all(r["qualifies"] for r in REFERENCES)
    assert [r["task_id"] for r in REFERENCES if r["optimal_cost"] < r["hindsight_cost"]] == [
        "dock-24B-w06x1-busy-0-e15", "dock-24B-w07x1-busy-0-e08"]
    assert [round(sum(r[k]["reward"] for r in REFERENCES) / len(REFERENCES), 3)
            for k in ("rolling", "silent", "naive")] == [0.564, 0.107, 0.075]


def test_the_follower_takes_each_counter_offer_at_once():
    offers = []
    for ref in REFERENCES:
        exchanges = replayed(PACK[ref["task_id"]], ref["rolling"]).exchanges
        for asked, then in zip(exchanges, [*exchanges[1:], None], strict=True):
            if not asked["reply"]["agreed"]:
                offers.append("earliest" if "earliest" in asked["reply"] else "latest")
                assert (then["watch"], then["ship"], then["arrival"], then["reply"]["agreed"]) == (
                    asked["watch"], asked["ship"], asked["reply"][offers[-1]], True)
    assert Counter(offers) == {"earliest": 203, "latest": 22}


@pytest.mark.parametrize("ref", REFS)
def test_the_hindsight_plan_grades_at_the_lower_bound_with_each_ship_slowed_from_the_watch_that_brings_its_news(ref):
    """Each ship arrives at its berth hour when it can, no earlier than at cruising speed and no later than the slowest
    it could still reach from the watch that brings its news, or from hour 0 for a ship with none: no ship waits that
    need not."""
    task = PACK[ref["task_id"]]
    plan, week, first = plan_from_list(task.reference["optimal_plan"]), LinesWeek(task), lines.first_known(task)
    assert set(first.values()) <= {w.hour for w in week.watches}
    arrivals = {}
    for s in task.ships:
        asked = first.get(s.id, 0)
        latest = s.arrival if asked >= s.arrival else week.reach(s.id, asked, s.arrival)[1]
        arrivals[s.id] = min(max(plan[s.id][0], s.arrival), latest)
    truth = lines.with_arrivals(task, arrivals, {s.id: s.arrival for s in task.ships})
    res = lines.evaluate(truth, plan)
    assert res.feasible and res.cost == ref["hindsight_cost"]
    waits = sum(truth.ships[r.ship].sections * (r.berth_hour - truth.ships[r.ship].arrival) for r in res.ships)
    assert res.cost == marine.evaluate(truth, plan).cost + waits
    assert (res.delay_cost, res.moves) == (res.cost - MOVE_PENALTY * res.moves, sum(r.moved for r in res.ships))


def test_a_week_qualifies_by_its_three_clauses_and_the_qualifying_weeks_are_the_task_ids():
    for ref in REFERENCES:
        clauses = {"a": sum(c["cost"] is not None for c in ref["configs"]) >= 3,
                   "b": sum(c["reward"] is not None and c["reward"] <= 0.9 for c in ref["silent"]["configs"]) >= 3,
                   "c": len(ref["watch_hours"]) <= 10}
        assert ref["clauses"] == clauses and ref["qualifies"] == all(clauses.values())
    assert lines.task_ids() == [r["task_id"] for r in REFERENCES if r["qualifies"]]
    assert set(lines.task_ids()) <= set(PACK)
