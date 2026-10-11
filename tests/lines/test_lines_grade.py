"""The lines grade (agentenv_portsim.lines.executed, evaluate and LinesWeek.finish): a window that starts before its
ship gets in begins when it does, an hour at anchor costs the ship's sections, first come first served unless the wind
holds the ship whose turn it is, an ETA that proved wrong is never excused, and the floor is the week's at cruising
speed."""

import pytest
from berth_core.check import unavoidable_cost
from berth_core.solve import naive_replan

from agentenv_portsim import lines, marine, world
from agentenv_portsim.lines import LinesWeek

PACK = lines.pack()
E15 = PACK.get("dock-24B-w06x1-busy-0-e15")
E09 = PACK.get("dock-24B-w07x1-busy-0-e09")
CRUISING = {s.id: s.arrival for s in E15.ships}
WEEKS = [pytest.param(t, id=t.task_id) for t in PACK.tasks]


def cruising(task):
    arrivals = {s.id: s.arrival for s in task.ships}
    return lines.with_arrivals(task, arrivals, arrivals)


def queue(res, ship: int) -> list[str]:
    return [p for p in res.ships[ship].problems if world.rule(p) == "queue"]


def problems(rows: list[dict]) -> list[tuple[int, str]]:
    return [(r["ship"], r["problem"]) for r in rows]


def test_with_arrivals_sets_each_ships_arrival_and_turn_and_nothing_else():
    task = lines.with_arrivals(E15, CRUISING | {3: 42}, CRUISING)
    assert [s.arrival for s in task.ships] == [CRUISING[s.id] if s.id != 3 else 42 for s in E15.ships]
    assert task.rules == E15.rules | {"lines": E15.rules["lines"] | {"turns": list(CRUISING.values())}}
    assert "turns" not in E15.rules["lines"]


def test_a_window_that_starts_before_its_ship_gets_in_begins_when_it_does():
    truth = cruising(E15)
    assert truth.ships[3].arrival == 36
    assert lines.executed(truth, {3: (30, 3, 1)}) == {3: (36, 3, 1)}
    assert lines.executed(truth, {3: (36, 3, 1), 4: (60, 7, 4)}) == {3: (36, 3, 1), 4: (60, 7, 4)}
    early, slid = marine.evaluate(truth, {3: (30, 3, 1)}).ships[3], lines.evaluate(truth, {3: (30, 3, 1)}).ships[3]
    assert [world.rule(p) for p in early.problems] == ["arrival"]
    on_time = marine.evaluate(truth, {3: (36, 3, 1)}).ships[3]
    assert (slid.berth_hour, slid.problems, slid.cost) == (36, [], on_time.cost)


def test_a_slid_window_also_waits_out_the_wind_that_holds_its_ship():
    """DALILA (334 m) getting in at 45 waits out the wind above 25 kn to 47 and STEEN (138 m) doesn't; at 98 NAVIOS
    INDIGO (261 m) waits out the hour above 30 kn and SEASPAN OCEANIA (334 m) the blow to 107. A window the planner
    set at or after the arrival is left alone."""
    held = lines.with_arrivals(E15, CRUISING | {1: 98, 2: 45, 3: 45, 4: 98}, CRUISING)
    assert (44, 47) in held.no_move_windows(held.ships[2]) and (44, 47) not in held.no_move_windows(held.ships[3])
    assert held.no_move_windows(held.ships[1]) == [(98, 99)] and (97, 107) in held.no_move_windows(held.ships[4])
    assert lines.executed(held, {1: (90, 9, 5), 2: (40, 7, 4), 3: (40, 3, 1), 4: (90, 7, 4)}) == {
        1: (99, 9, 5), 2: (47, 7, 4), 3: (45, 3, 1), 4: (107, 7, 4)}
    truth = cruising(E15)
    assert lines.executed(truth, {2: (45, 7, 4)}) == {2: (45, 7, 4)}
    assert "no_move" in [world.rule(p) for p in lines.evaluate(truth, {2: (45, 7, 4)}).ships[2].problems]


def test_executed_passes_unknown_ship_ids_through():
    plan = {3: (30, 3, 1), len(E15.ships): (5, 2, 2), 99: (0, 4, 1), -1: (3, 1, 1)}
    assert lines.executed(cruising(E15), plan) == plan | {3: (36, 3, 1)}


@pytest.mark.parametrize("task", WEEKS)
def test_an_hour_at_anchor_costs_the_ships_sections_as_an_hour_late_does(task):
    truth = cruising(task)
    plan = naive_replan(truth)
    assert lines.executed(truth, plan) == plan
    ours, theirs = lines.evaluate(truth, plan), marine.evaluate(truth, plan)
    waits = {s.id: max(0, plan[s.id][0] - s.arrival) for s in truth.ships}
    assert any(waits.values())
    for r, was in zip(ours.ships, theirs.ships, strict=True):
        assert r.cost == was.cost + truth.ships[r.ship].sections * waits[r.ship]
        assert [p for p in r.problems if world.rule(p) != "queue"] == was.problems
    assert lines.anchor_hours(truth, ours) == sum(waits.values())


@pytest.mark.parametrize("task", WEEKS)
def test_the_grade_runs_each_window_from_when_its_ship_gets_in_and_never_charges_the_arrival_rule(task):
    week = world.play(task, world.naive, week=LinesWeek)
    truth = week.truth()
    run = lines.executed(truth, week.plan)
    graded, plain = lines.evaluate(truth, week.plan), marine.evaluate(truth, run)
    assert [r.berth_hour for r in graded.ships] == [run[s.id][0] for s in truth.ships]
    for r, was in zip(graded.ships, plain.ships, strict=True):
        waited = max(0, r.berth_hour - truth.ships[r.ship].arrival)
        assert r.cost == was.cost + truth.ships[r.ship].sections * waited
    rules = {world.rule(v["problem"]) for v in week.grade["violations"] + week.grade["excused"]}
    assert "arrival" not in rules
    assert {s for s in week.plan if run[s] != week.plan[s]} == {
        r.ship for r in marine.evaluate(truth, week.plan).ships if any(world.rule(p) == "arrival" for p in r.problems)}


def test_no_ship_starts_while_one_earlier_in_the_queue_waits_at_anchor_unless_the_wind_holds_it():
    """CMA CGM DALILA (334 m, turn 24) waits at anchor for hour 47; STEEN (138 m, turn 36) may not berth before it at
    hour 43, but may at 45, when the wind above 25 kn holds the long ship and not the short one."""
    truth = cruising(E15)
    dalila, steen = truth.ships[2], truth.ships[3]
    assert (dalila.length_m >= 300 > steen.length_m, dalila.arrival, steen.arrival) == (True, 24, 36)
    assert (44, 47) in truth.no_move_windows(dalila) and (44, 47) not in truth.no_move_windows(steen)
    jumped = lines.evaluate(truth, {2: (47, 7, 4), 3: (43, 3, 1)})
    line = "berths at hour 43 while ship 2 CMA CGM DALILA, earlier in the queue, waits at anchor"
    assert queue(jumped, 3) == [line] and queue(jumped, 2) == [] and not jumped.feasible
    assert world.rule(line) == "queue" and ("queue", r"earlier in the queue") in world.RULES
    assert queue(lines.evaluate(truth, {2: (47, 7, 4), 3: (45, 3, 1)}), 3) == []
    assert queue(lines.evaluate(truth, {2: (47, 7, 4), 3: (48, 3, 1)}), 3) == []
    assert queue(lines.evaluate(truth, {2: (47, 7, 4), 3: (36, 3, 1)}), 3) == [
        "berths at hour 36 while ship 2 CMA CGM DALILA, earlier in the queue, waits at anchor"]


def test_a_slowed_ship_keeps_its_turn_but_waits_in_the_queue_only_once_it_has_arrived():
    slowed = lines.with_arrivals(E15, CRUISING | {3: 50}, CRUISING)
    assert (slowed.ships[3].arrival, slowed.rules["lines"]["turns"][3], slowed.ships[4].arrival) == (50, 36, 48)
    assert queue(lines.evaluate(slowed, {3: (60, 3, 1), 4: (50, 7, 4)}), 4) == [
        "berths at hour 50 while ship 3 STEEN, earlier in the queue, waits at anchor"]
    assert queue(lines.evaluate(slowed, {3: (60, 3, 1), 4: (49, 7, 4)}), 4) == []
    by_arrival = lines.with_arrivals(E15, CRUISING | {3: 50}, CRUISING | {3: 50})
    assert queue(lines.evaluate(by_arrival, {3: (60, 3, 1), 4: (50, 7, 4)}), 4) == []
    assert queue(lines.evaluate(by_arrival, {3: (60, 3, 1), 4: (50, 7, 4)}), 3) == []


def test_only_the_first_ship_jumped_is_named():
    truth = cruising(E15)
    res = lines.evaluate(truth, {1: (40, 9, 5), 2: (47, 7, 4), 3: (38, 3, 1)})
    assert queue(res, 3) == ["berths at hour 38 while ship 1 NAVIOS INDIGO, earlier in the queue, waits at anchor"]


def test_an_eta_that_proved_wrong_is_charged_while_the_wind_no_forecast_showed_is_still_excused():
    """Naive on e09: CARLOTA B's window froze at hour 87, the ETA its delay notice gave; it got in at 93, so its window
    began then, and the lateness and the pilots it then lacked are charged, as the week as known then holds them too
    with the truth's arrivals. MAERSK NUBA got in at 58 into wind no forecast showed: the wait to 62 and the tugs short
    then are excused."""
    views = []

    def policy(week: LinesWeek):
        views.append(week.view)
        return world.naive(week)

    week = world.play(E09, policy, week=LinesWeek)
    truth, plan = week.truth(), week.plan
    run = lines.executed(truth, plan)

    def then(sid: int):
        decided = next(k for k, f in enumerate(week.frozen) if sid in f["ships"]) - 1
        known = week.past([e["event_id"] for e in week.log if e["watch"] <= decided], truth)
        return views[decided], known

    eta, known = then(7)
    assert (plan[7], next(s.arrival for s in eta.ships if s.id == 7), truth.ships[7].arrival, run[7]) == (
        (87, 3, 1), 87, 93, (93, 3, 1))
    assert lines.evaluate(eta, plan).ships[7].problems == []
    late = lines.evaluate(truth, plan).ships[7]
    assert late.problems == lines.evaluate(known, plan).ships[7].problems == [
        "pilots short at hour 93: your ships need 2, 1 free"]
    assert late.cost > lines.evaluate(eta, plan).ships[7].cost
    assert {(7, late.problems[0]), (8, late.problems[0])} <= set(problems(week.grade["violations"]))
    assert 7 not in week.excuses()[1]
    _, known = then(16)
    nuba = (lines.evaluate(known, plan).ships[16], lines.evaluate(truth, plan).ships[16])
    assert (plan[16], truth.ships[16].arrival, run[16], nuba[0].berth_hour) == ((57, 2, 2), 58, (62, 2, 2), 58)
    assert (57, 62) in truth.no_move_windows(truth.ships[16])
    assert week.excuses()[1] == {16: nuba[1].cost - nuba[0].cost} and week.grade["excused_cost"] == 20
    assert (16, "tugs short at hour 62: your ships need 3, 0 free") in problems(week.grade["excused"])
    assert {world.rule(p) for _, p in problems(week.grade["excused"])} == {"no_move", "tugs"}
    assert not week.grade["feasible"]


@pytest.mark.parametrize("task", WEEKS)
def test_in_the_naive_weeks_no_queue_break_is_excused_and_the_grade_is_the_truths(task):
    week = world.play(task, world.naive, week=LinesWeek)
    assert "queue" not in {world.rule(p) for _, p in problems(week.grade["excused"])}
    truth = week.truth()
    graded = lines.evaluate(truth, week.plan)
    assert sorted(problems(week.grade["violations"]) + problems(week.grade["excused"])) == sorted(
        (r.ship, p) for r in graded.ships for p in r.problems)
    assert week.grade["raw_cost"] == sum(r.cost for r in graded.ships)
    assert week.grade["anchor_hours"] == lines.anchor_hours(truth, graded)


@pytest.mark.parametrize("task", WEEKS)
def test_the_floor_is_the_weeks_unavoidable_cost_at_cruising_speed(task):
    week = world.play(task, world.naive, week=LinesWeek)
    assert week.grade["unavoidable_cost"] == unavoidable_cost(cruising(task)) == unavoidable_cost(task)
    assert week.grade["optimal_cost"] == task.reference["optimal_cost"]


def test_slowing_a_ship_does_not_move_the_floor():
    def policy(week: LinesWeek):
        if week.watch == 0:
            week.request("globalliner", 3, 42)
        return world.naive(week)

    week = world.play(E15, policy, week=LinesWeek)
    assert (week.truth().ships[3].arrival, unavoidable_cost(week.truth())) == (42, 52)
    assert week.grade["unavoidable_cost"] == unavoidable_cost(E15) == 48
