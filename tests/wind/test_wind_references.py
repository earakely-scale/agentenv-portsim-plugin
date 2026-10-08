"""The wind pack and its references (here the fixtures scripts/wind_references.py built from synthetic weather),
replayed without ortools: the stored plans reproduce their grades and respect their own views, the clauses decide a
pair, and the anchor is the lower of the hindsight optimum and the follower's best net cost."""

import hashlib
import json
from collections.abc import Iterator
from dataclasses import replace

import berth_core
import pytest
from berth_core import TaskPack, plan_from_list
from berth_core.check import unavoidable_cost
from berth_core.reward import score_v3
from wind_fixtures import (
    BUST_TASK,
    FIXTURES,
    OTHER_TASK,
    PACK_DIR,
    REFERENCES,
    STORM_TASK,
    WEATHER,
    tasks_dir,
    use,
)

from agentenv_portsim import marine, wind, world
from agentenv_portsim.schedule import schedule
from agentenv_portsim.wind import WindWeek

PACK = TaskPack(PACK_DIR)
TASKS = {t.task_id: t for t in PACK.tasks}
REFS = [json.loads(line) for line in REFERENCES.read_text().splitlines()]
BY_ID = {r["task_id"]: r for r in REFS}
WEEKS = {w["id"]: w for w in map(json.loads, WEATHER.read_text().splitlines())}
MANIFEST = json.loads((PACK_DIR / "manifest.json").read_text())
CONFIGS = [(1, True), (1, False), (8, True), (8, False)]
OUTCOME = ("cost", "reward", "feasible", "excused_cost")


def outcome(week: world.Week) -> dict:
    return {key: week.grade[key] for key in OUTCOME}


def views(week: WindWeek) -> dict[str, berth_core.Task]:
    """The week as each re-planner saw it: the follower as known, the blind one without the wind, the
    hold-every-warning one with every window any delivered forecast showed."""
    view = week.view
    return {"rolling": view, "blind": replace(view, rules=view.rules | {"no_moves": []}), "hold": wind.held(week)}


def played_through(task: berth_core.Task) -> Iterator[WindWeek]:
    """The week at each of its watches, its news delivered, with no plan."""
    week = WindWeek(task)
    while True:
        yield week
        if week.last:
            return
        week.open()
        for n in week.watches[week.watch].notices:
            week.notice(n.event_id, n.name, n.text, "trigger")


def test_the_fixture_pack_is_the_hand_deal_in_schedule_order():
    deal = json.loads((FIXTURES / "deal.json").read_text())
    assert [f"{d['schedule']}-{d['weather']}" for d in deal] == list(TASKS) == [r["task_id"] for r in REFS]
    assert list(TASKS) == [STORM_TASK, BUST_TASK, OTHER_TASK]
    assert [(r["kind"], r["qualifies"]) for r in REFS] == [("storm", True), ("bust", True), ("storm", False)]


def test_the_manifest():
    body = (PACK_DIR / "tasks.jsonl").read_bytes()
    assert list(MANIFEST) == ["name", "split", "tasks", "tiers", "sha256", "weeks", "quays", "source", "marine",
                              "weather", "pairs", "ecmwf", "y7", "calibration", "wind", "deal", "note"]
    assert {key: MANIFEST[key] for key in ("name", "split", "tasks", "tiers", "weeks", "quays")} == {
        "name": "dock-v1-wind", "split": "eval", "tasks": 3, "tiers": {"busy": 2, "standard": 1}, "weeks": [7, 37],
        "quays": {"24B": 2, "36A": 1}}
    assert MANIFEST["sha256"] == hashlib.sha256(body).hexdigest()
    assert body == b"".join(json.dumps(t.to_dict(), ensure_ascii=False, separators=(",", ":")).encode() + b"\n"
                            for t in PACK.tasks)
    assert MANIFEST["marine"] == {"pack": "dock-v1-marine", "sha256": marine.pack().manifest["sha256"]}
    assert MANIFEST["weather"] == {"file": "wind/weather.jsonl", "records": 2,
                                   "sha256": hashlib.sha256(WEATHER.read_bytes()).hexdigest()}
    assert MANIFEST["pairs"] == [
        {"task_id": r["task_id"], "schedule": r["schedule"], "weather": r["weather"], "kind": r["kind"],
         "iso_week": WEEKS[r["weather"]]["iso_week"], "added_watches": r["added_watches"],
         "windows": WEEKS[r["weather"]]["windows"]} for r in REFS]
    sources = json.loads((FIXTURES / "wind/weather-sources.json").read_text())
    assert {key: MANIFEST[key] for key in ("ecmwf", "y7", "calibration")} == sources
    assert list(MANIFEST["wind"]) == ["grounding"]
    for key, item in MANIFEST["wind"]["grounding"].items():
        assert list(item) == ["value", "basis"]
        assert "https://" in item["basis"] or "Assumption" in item["basis"], key
    assert MANIFEST["deal"] == {"screened": 4, "qualifying": 2, "dealt": 3, "gate": 12}


@pytest.mark.parametrize("ref", REFS, ids=lambda r: r["task_id"])
def test_the_record(ref):
    task = TASKS[ref["task_id"]]
    v3 = marine.pack().get(ref["schedule"])
    assert list(ref) == ["task_id", "schedule", "weather", "kind", "watch_hours", "added_watches", "optimal_cost",
                         "hindsight_cost", "v3_optimal_cost", "unavoidable_cost", "rolling", "configs", "blind"] + (
        ["hold"] if ref["kind"] == "bust" else []) + ["naive", "clauses", "qualifies", "solver"]
    assert ref["watch_hours"] == [w.hour for w in WindWeek(task).watches] == wind.watch_hours(v3, WEEKS[ref["weather"]])
    assert ref["added_watches"] == [h for h in ref["watch_hours"] if h not in [w.hour for w in schedule(v3)]]
    assert (ref["v3_optimal_cost"], ref["unavoidable_cost"]) == (v3.reference["optimal_cost"], unavoidable_cost(task))
    hindsight = marine.evaluate(task, plan_from_list(task.reference["optimal_plan"]))
    assert hindsight.feasible and hindsight.cost == ref["hindsight_cost"] == task.reference["lower_bound"]
    assert ref["optimal_cost"] == task.reference["optimal_cost"] == min(
        [ref["hindsight_cost"]] + [c["cost"] for c in ref["configs"] if c["cost"] is not None])
    assert ref["solver"] == {"ortools": "9.15.6755", "max_deterministic_time": 60.0}
    for rows in [ref["configs"]] + [ref[mode]["configs"] for mode in ("blind", "hold") if mode in ref]:
        assert [(c["workers"], c["tiebreak"]) for c in rows] == CONFIGS
    assert ref["rolling"]["config"] == next(k for k, c in enumerate(ref["configs"]) if "error" not in c)


@pytest.mark.parametrize("ref", REFS, ids=lambda r: r["task_id"])
def test_the_clauses_decide_the_pair(ref):
    task, clauses = TASKS[ref["task_id"]], ref["clauses"]
    other = ref["blind" if ref["kind"] == "storm" else "hold"]["configs"]
    assert clauses == {
        "a": sum(c["cost"] is not None and c["cost"] <= ref["hindsight_cost"] for c in ref["configs"]) >= 3,
        "b": sum(c["reward"] is not None and c["reward"] <= 0.9 for c in other) >= 3,
        "c": len(ref["watch_hours"]) <= 9,
        "d": not any(w["start"] <= b.end < w["end"] for b in task.blocks if b.kind == "alongside"
                     for w in task.rules["no_moves"] if w["min_length"] == 0)}
    assert ref["qualifies"] is all(clauses.values())


@pytest.mark.parametrize("ref", REFS, ids=lambda r: r["task_id"])
def test_every_stored_plan_replays_to_its_grade_against_the_anchor(ref):
    task = TASKS[ref["task_id"]]
    for mode in ("rolling", "blind", "hold"):
        if mode not in ref:
            continue
        stored = ref[mode]
        week = world.play(task, lambda w, plans=stored["plans"]: plan_from_list(plans[w.watch]), week=WindWeek)
        assert week.refusals == [] and len(stored["plans"]) == len(week.watches)
        assert outcome(week) == {key: stored[key] for key in OUTCOME}, mode
        if week.grade["feasible"]:
            reward = score_v3(week.grade["cost"], True, 1.0, ref["optimal_cost"], 100, ref["unavoidable_cost"])[0]
            assert week.grade["reward"] == round(reward, 6)
        configs = ref["configs"] if mode == "rolling" else stored["configs"]
        assert {key: configs[stored["config"]][key] for key in ("cost", "reward")} == {
            key: stored[key] for key in ("cost", "reward")}
    first, second = (world.play(task, world.naive, week=WindWeek) for _ in range(2))
    assert outcome(first) == outcome(second) == ref["naive"] and first.plan == second.plan


@pytest.mark.parametrize("ref", REFS, ids=lambda r: r["task_id"])
def test_every_stored_plan_keeps_its_open_ships_clear_on_the_view_it_was_solved_on(ref):
    """Under forecast relief only the frozen windows may break a rule on the re-planner's view."""
    task = TASKS[ref["task_id"]]
    for mode in ("rolling", "blind", "hold"):
        if mode not in ref:
            continue
        plans = ref[mode]["plans"]
        week = WindWeek(task)
        while True:
            plan = plan_from_list(plans[week.watch])
            fixed = week.fixed
            res = marine.evaluate(views(week)[mode], plan)
            assert [(r.ship, r.problems) for r in res.ships if r.problems and r.ship not in fixed] == [], (
                mode, week.hour)
            week.confirm(plans[week.watch])
            if week.last:
                break
            week.open()
            for n in week.watches[week.watch].notices:
                week.notice(n.event_id, n.name, n.text, "trigger")


def test_the_hold_view_holds_each_hour_any_delivered_forecast_showed_once():
    """A movement inside two overlapping windows would take two wind tugs in marine_references' pools."""
    overlapping = 0
    for week in played_through(TASKS[BUST_TASK]):
        observed = wind.forecast(week.view)["observed"]
        held = wind.held(week).rules["no_moves"]
        assert held[:len(observed)] == observed
        shown = [week.scheduled[i].event for i in week.revealed if week.scheduled[i].kind == "forecast"]
        for min_length, _ in wind.THRESHOLDS:
            ours = [range(w["start"], w["end"]) for w in held[len(observed):] if w["min_length"] == min_length]
            theirs = [range(max(w["start"], week.hour), w["end"]) for e in shown for w in e["windows"]
                      if w["min_length"] == min_length]
            assert sum(map(len, ours)) == len(set().union(*ours)) and set().union(*ours) == set().union(*theirs)
            overlapping += sum(map(len, theirs)) > len(set().union(*theirs))
    assert overlapping


def test_the_follower_beats_hindsight_net_of_excuses_so_the_anchor_is_its_cost():
    ref, task = BY_ID[STORM_TASK], TASKS[STORM_TASK]
    assert (ref["optimal_cost"], ref["hindsight_cost"], ref["rolling"]["cost"], ref["rolling"]["excused_cost"]) == (
        234, 244, 234, 96)
    hindsight = plan_from_list(task.reference["optimal_plan"])
    graded = world.grade_week(task, hindsight, (), {}, evaluate=marine.evaluate)
    assert graded["feasible"] and graded["cost"] == 244 > ref["optimal_cost"]
    assert graded["reward"] == round(score_v3(244, True, 1.0, 234, 100, 177)[0], 6) < 1.0
    assert graded["regret"] == 10
    on_hindsight = replace(task, reference=task.reference | {"optimal_cost": ref["hindsight_cost"]})
    assert world.grade_week(on_hindsight, hindsight, (), {}, evaluate=marine.evaluate)["reward"] == 1.0
    assert ref["rolling"]["reward"] == 1.0


def test_the_wind_pack_and_its_references_load_through_the_module(monkeypatch, tmp_path):
    use(monkeypatch)
    assert [t.task_id for t in wind.pack().tasks] == list(TASKS)
    assert wind.references() == REFS and wind.task_ids() == [STORM_TASK, BUST_TASK]
    monkeypatch.undo()
    monkeypatch.setenv("BERTH_TASKS_DIR", tasks_dir(tmp_path))
    assert wind.pack_dir().resolve() == PACK_DIR.resolve()
    assert [t.task_id for t in wind.pack().tasks] == list(TASKS)
    assert berth_core.TaskPack().get("dock-36A-w37x1-standard-0").task_id == "dock-36A-w37x1-standard-0"
