"""The lines pack (agentenv_portsim.lines): the wind weeks with each ship's agent and the arrival news given as the
agents' ETAs, the ETA model, and the agents' reports carried by v4's watches with no watch added and no news given
early."""

import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from agentenv_portsim import lines, wind
from agentenv_portsim.schedule import LINES_PACK, schedule

PACK = lines.pack()
WIND = wind.pack()
MANIFEST = json.loads((lines.pack_dir() / "manifest.json").read_text())
E15 = PACK.get("dock-24B-w06x1-busy-0-e15")
WEEKS = [pytest.param(t, id=t.task_id) for t in PACK.tasks]


def reports(watch) -> list:
    return [n for n in watch.notices if n.kind in lines.REPORTS]


def news(task) -> dict[int, list[tuple[int, int]]]:
    """Each late, bunched or unscheduled ship and the (watch, hour) of each v4 notice about it."""
    out: dict[int, list[tuple[int, int]]] = {}
    for w in schedule(task):
        for n in w.notices:
            if n.kind in lines.NEWS_ETA:
                for s in [n.event["ship"]] if n.kind != "bunching" else n.event["ships"]:
                    out.setdefault(s, []).append((w.index, n.hour))
    return out


def test_the_pack_sits_beside_the_first_tasks_dir_or_in_the_package(monkeypatch):
    first = Path(os.environ["BERTH_TASKS_DIR"].split(":")[0])
    assert lines.pack_dir() == first.parent / LINES_PACK
    monkeypatch.delenv("BERTH_TASKS_DIR")
    assert Path(lines.pack_dir()).resolve() == (first.parent / LINES_PACK).resolve()
    assert [t.task_id for t in lines.pack().tasks] == [t.task_id for t in PACK.tasks]


def test_the_manifest_pins_the_pack_and_the_wind_pack_it_was_made_from():
    body = (lines.pack_dir() / "tasks.jsonl").read_bytes()
    assert {key: MANIFEST[key] for key in ("name", "split", "tasks", "tiers", "quays")} == {
        "name": "dock-v1-lines", "split": "eval", "tasks": 15, "tiers": {"busy": 12, "standard": 3},
        "quays": {"24B": 7, "36A": 8}}
    assert MANIFEST["sha256"] == hashlib.sha256(body).hexdigest()
    assert MANIFEST["wind"] == {"pack": "dock-v1-wind", "sha256": hashlib.sha256(
        (wind.pack_dir() / "tasks.jsonl").read_bytes()).hexdigest()}
    assert list(MANIFEST["lines"]["grounding"]) == ["agents", "reports", "eta_error", "speeds", "queue", "anchor"]
    assert all(list(item) == ["value", "basis"] for item in MANIFEST["lines"]["grounding"].values())


@pytest.mark.parametrize("task", WEEKS)
def test_a_lines_week_is_its_wind_week_with_the_agents_and_the_news_as_their_etas(task):
    """Only rules.lines, the reference and the late, bunching and unscheduled-call news differ: each now carries the
    agent's ETA as of the watch it reaches the planner, never at or before the slot a delayed ship is late for."""
    v4 = WIND.get(task.task_id)
    assert replace(task, rules={}, reference={}, disruptions=[], notices=[]) == replace(
        v4, rules={}, reference={}, disruptions=[], notices=[])
    assert {k: v for k, v in task.rules.items() if k != "lines"} == v4.rules
    firms = task.rules["lines"]["firms"]
    assert list(task.rules["lines"]) == ["firms", "ships"] and list(firms) == sorted(firms)
    assert len(task.rules["lines"]["ships"]) == len(task.ships)
    assert {lines.firm(task, s.id) for s in task.ships} == set(firms)
    at = {n.event_id: w.hour for w in schedule(v4) for n in w.notices}
    for i, (e, text, was, was_text) in enumerate(zip(task.disruptions, task.notices, v4.disruptions, v4.notices,
                                                     strict=True)):
        hour = at[f"{was['type']}-{i}"]
        if was["type"] == "late":
            slot = task.ships[was["ship"]].arrival - was["hours"]
            assert e == was | {"eta": max(lines.estimate(task, was["ship"], hour), slot + 1)}
            assert f"its agent now gives ETA hour {e['eta']} (planned slot hour" in text
        elif was["type"] == "extra":
            assert e == was | {"eta": lines.estimate(task, was["ship"], hour)}
            assert f"has ETA hour {e['eta']} from its agent" in text
        elif was["type"] == "bunching":
            assert e == was | {"etas": [max(lines.estimate(task, s, hour), task.ships[s].planned_hour + 1)
                                        for s in was["ships"]]}
            assert "their agents' ETAs: " + ", ".join(
                f"ship {s} hour {x}" for s, x in zip(e["ships"], e["etas"], strict=True)) in text
        else:
            assert (e, text) == (was, was_text)


def test_a_delay_notice_never_gives_an_eta_at_or_before_the_slot_the_ship_is_late_for():
    seen = []
    for task in PACK.tasks:
        at = {n.event_id: w.hour for w in schedule(task) for n in w.notices}
        for i, e in enumerate(task.disruptions):
            if e["type"] == "late":
                rows = [(e["ship"], e["eta"], task.ships[e["ship"]].arrival - e["hours"])]
            elif e["type"] == "bunching":
                rows = [(s, x, task.ships[s].planned_hour) for s, x in zip(e["ships"], e["etas"], strict=True)]
            else:
                continue
            for sid, eta, slot in rows:
                seen.append((eta, slot, lines.estimate(task, sid, at[f"{e['type']}-{i}"]), task.ships[sid].arrival))
    assert all(slot < eta == max(raw, slot + 1) for eta, slot, raw, _ in seen)
    assert [(eta, slot, raw, truth) for eta, slot, raw, truth in seen if raw <= slot and truth < eta] == []
    assert sum(raw <= slot for _, slot, raw, _ in seen) >= 5


def test_each_ships_agent_and_how_far_off_it_is():
    assert E15.rules["lines"]["firms"] == {
        "aperez": "A. Pérez y Cía", "boluda": "Boluda Lines", "cmacgm": "CMA CGM Ibérica",
        "cosco": "COSCO Shipping Lines Spain", "globalliner": "Global Liner Agencias", "hapag": "Hapag-Lloyd Spain",
        "noatum": "Noatum Maritime", "one": "Ocean Network Express Spain"}
    assert lines.meta(E15, 3) == {"firm": "globalliner", "leg_nm": 165, "bias": 0.739}
    assert (lines.firm(E15, 3), lines.firm_name(E15, "globalliner")) == ("globalliner", "Global Liner Agencias")
    assert lines.leg_hours(E15, 3) == 165 / 17 and lines.departure(E15, 3) == 36 - 165 / 17
    elbspirit = PACK.get("dock-36A-w06x1-busy-0-e07")
    assert (elbspirit.ships[10].from_port, lines.leg_hours(elbspirit, 10), lines.departure(elbspirit, 10)) == (
        "Monrovia", None, None)
    biases = [m["bias"] for t in PACK.tasks for m in t.rules["lines"]["ships"]]
    assert max(map(abs, biases)) <= 4 and 0.75 <= sum(b > 0 for b in biases) / len(biases) <= 0.85


@pytest.mark.parametrize("task", WEEKS)
def test_an_eta_is_never_before_the_next_hour_shrinks_toward_arrival_and_is_exact_from_the_call(task):
    for s in task.ships:
        errors = []
        for hour in range(-48, s.arrival + 1):
            eta = lines.estimate(task, s.id, hour)
            assert eta == s.arrival if s.arrival - hour <= lines.CALL_LEAD else eta >= hour + 1
            errors.append(abs(eta - s.arrival))
        assert errors == sorted(errors, reverse=True), s.id


def test_etas_are_mostly_early_by_a_share_of_the_hours_left():
    assert [lines.estimate(E15, 3, h) for h in (0, 12, 24, 34, 35, 36)] == [31, 32, 34, 36, 36, 36]
    assert [lines.estimate(E15, 1, h) for h in (-41, -17, 0, 5, 6)] == [17, 12, 8, 7, 7]
    assert lines.meta(E15, 1)["bias"] < 0 < lines.meta(E15, 3)["bias"]


@pytest.mark.parametrize("task", WEEKS)
def test_the_timetable_is_v4s_watches_each_with_the_reports_made_since_the_watch_before(task):
    v4, ours = schedule(task), lines.timetable(task)
    hours = [w.hour for w in v4]
    assert [(w.index, w.hour) for w in ours] == [(w.index, w.hour) for w in v4]
    for w, was in zip(ours, v4, strict=True):
        assert w.notices[:len(was.notices)] == was.notices
        assert {n.kind for n in w.notices[len(was.notices):]} <= set(lines.REPORTS)
        made = reports(w)
        assert made == sorted(made, key=lambda n: (n.hour, n.event_id))
        for n in made:
            e, s = n.event, task.ships[n.event["ship"]]
            assert w.index == next(k for k, h in enumerate(hours) if h >= e["hour"])
            assert (e["type"], n.hour, n.event_hour, n.index) == (n.kind, e["hour"], s.arrival, -1)
            assert e["hour"] == max(s.arrival - e["lead"], 0)
            assert n.event_id == f"{n.kind}-{s.id}-{e['lead']}"
            assert e["lead"] == lines.CALL_LEAD if n.kind == "call" else e["lead"] in lines.REPORT_LEADS
            assert e["eta"] == (s.arrival if n.kind == "call" else lines.estimate(task, s.id, e["hour"]))
            assert (n.name, n.text) == (lines.firm_name(task, lines.firm(task, s.id)), lines.report_text(task, e))


@pytest.mark.parametrize("task", WEEKS)
def test_every_ship_due_by_the_last_watch_calls_in_and_the_week_opens_with_the_latest_report_made_before_it(task):
    made = [n for w in lines.timetable(task) for n in reports(w)]
    last = lines.timetable(task)[-1].hour
    assert sorted(n.event["ship"] for n in made if n.kind == "call") == [
        s.id for s in task.ships if s.arrival - lines.CALL_LEAD <= last]
    news = lines.first_known(task)
    for s in task.ships:
        opening = [n for n in made if n.event["ship"] == s.id and s.arrival - n.event["lead"] <= 0]
        leads = [lead for lead in (*lines.REPORT_LEADS, lines.CALL_LEAD) if s.arrival - lead <= 0]
        assert [n.event["lead"] for n in opening] == ([] if s.id in news or not leads else [min(leads)])


@pytest.mark.parametrize("task", WEEKS)
def test_no_report_about_a_late_bunched_or_unscheduled_ship_comes_before_the_news_of_it(task):
    told = news(task)
    assert lines.first_known(task) == {s: max(h for _, h in notices) for s, notices in told.items()}
    for w in lines.timetable(task):
        for n in reports(w):
            if (s := n.event["ship"]) in told:
                assert n.hour > lines.first_known(task)[s] and w.index > max(k for k, _ in told[s])


def test_the_reports_of_one_week_watch_by_watch():
    watches = lines.timetable(E15)
    assert [(w.hour, [n.event_id for n in reports(w)]) for w in watches] == [
        (0, ["call-0-1", "eta-1-24", "eta-2-24", "eta-3-48", "eta-4-48"]),
        (24, ["call-1-1", "eta-3-24", "call-2-1", "eta-4-24"]),
        (30, []),
        (42, ["call-3-1", "eta-7-48"]),
        (72, ["call-4-1", "eta-6-24", "eta-8-48", "eta-5-24", "eta-7-24", "eta-9-48", "call-16-1", "call-6-1"]),
        (96, ["call-5-1", "eta-10-48", "eta-8-24", "eta-11-48", "call-7-1", "eta-9-24", "eta-12-48", "call-8-1"])]
    assert lines.first_known(E15) == {5: 30, 6: 42, 16: 45}
    opening = reports(watches[0])
    assert [(n.name, n.text) for n in (opening[0], opening[3])] == [
        ("A. Pérez y Cía", "PERSEUS (ship 0) calls in: at buoy S, arriving hour 0 (Mon 00:00)."),
        ("Global Liner Agencias", "STEEN (ship 3): ETA Tue 07:00 (hour 31), as of Mon 00:00.")]
    assert reports(watches[1])[1].text == "STEEN (ship 3): ETA Tue 08:00 (hour 32), as of Mon 12:00."
    assert opening[1].event == {"type": "eta", "ship": 1, "hour": 0, "lead": 24, "eta": 8}
