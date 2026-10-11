"""The lines pack (agentenv_portsim.lines): the wind weeks with each ship's agent, each arrival off its published
schedule by the agent's long-range error and the arrival news given as the agents' ETAs, the ETA model, and the agents'
reports carried by v4's watches with no watch added and no news given early."""

import hashlib
import json
import os
from collections import Counter
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
def test_a_lines_week_is_its_wind_week_with_the_agents_the_arrivals_off_schedule_and_the_news_as_their_etas(task):
    """Only the arrivals, rules.lines, the reference and the late, bunching and unscheduled-call news differ: each now
    carries the agent's ETA as of the watch it reaches the planner, never at or before the hour a delayed ship would
    have arrived without it."""
    v4 = WIND.get(task.task_id)
    assert replace(lines.as_v4(task), rules={}, reference={}, disruptions=[], notices=[]) == replace(
        v4, rules={}, reference={}, disruptions=[], notices=[])
    assert {k: v for k, v in task.rules.items() if k != "lines"} == v4.rules
    firms = task.rules["lines"]["firms"]
    assert list(task.rules["lines"]) == ["firms", "ships"] and list(firms) == sorted(firms)
    assert [list(m) for m in task.rules["lines"]["ships"]] == [
        ["firm", "leg_nm", "bias", "scheduled", "before_news", "v4_arrival"]] * len(task.ships)
    assert {lines.firm(task, s.id) for s in task.ships} == set(firms)
    at = {n.event_id: w.hour for w in schedule(v4) for n in w.notices}
    for i, (e, text, was, was_text) in enumerate(zip(task.disruptions, task.notices, v4.disruptions, v4.notices,
                                                     strict=True)):
        hour = at[f"{was['type']}-{i}"]
        if was["type"] == "late":
            before = lines.before_news(task, was["ship"])
            assert e == was | {"eta": max(lines.estimate(task, was["ship"], hour), before + 1)}
            assert text == was_text.replace("was delayed leaving", "is running late from").replace(
                f"it now arrives at hour {v4.ships[was['ship']].arrival}", f"its agent now gives ETA hour {e['eta']}")
        elif was["type"] == "extra":
            assert e == was | {"eta": lines.estimate(task, was["ship"], hour)}
            assert f"has ETA hour {e['eta']} from its agent" in text
        elif was["type"] == "bunching":
            assert e == was | {"etas": [max(lines.estimate(task, s, hour), lines.before_news(task, s) + 1)
                                        for s in was["ships"]]}
            assert "their agents' ETAs: " + ", ".join(
                f"ship {s} hour {x}" for s, x in zip(e["ships"], e["etas"], strict=True)) in text
        else:
            assert (e, text) == (was, was_text)


def test_a_delay_notice_never_gives_an_eta_at_or_before_the_hour_the_ship_would_have_arrived_without_it():
    seen = []
    for task in PACK.tasks:
        at = {n.event_id: w.hour for w in schedule(lines.as_v4(task)) for n in w.notices}
        for i, e in enumerate(task.disruptions):
            if e["type"] == "late":
                rows = [(e["ship"], e["eta"])]
            elif e["type"] == "bunching":
                rows = list(zip(e["ships"], e["etas"], strict=True))
            else:
                continue
            for sid, eta in rows:
                seen.append((eta, lines.before_news(task, sid), lines.estimate(task, sid, at[f"{e['type']}-{i}"]),
                             task.ships[sid].arrival))
    assert all(before < eta == max(raw, before + 1) for eta, before, raw, _ in seen)
    assert [(eta, before, raw, truth) for eta, before, raw, truth in seen if raw <= before and truth < eta] == []
    assert (len(seen), sum(raw <= before for _, before, raw, _ in seen)) == (57, 15)


def test_each_ships_agent_and_how_far_off_it_is():
    assert E15.rules["lines"]["firms"] == {
        "aperez": "A. Pérez y Cía", "boluda": "Boluda Lines", "cmacgm": "CMA CGM Ibérica",
        "cosco": "COSCO Shipping Lines Spain", "globalliner": "Global Liner Agencias", "hapag": "Hapag-Lloyd Spain",
        "noatum": "Noatum Maritime", "one": "Ocean Network Express Spain"}
    assert lines.meta(E15, 3) == {"firm": "globalliner", "leg_nm": 165, "bias": 0.739, "scheduled": 36,
                                  "before_news": None, "v4_arrival": 36}
    assert (lines.firm(E15, 3), lines.firm_name(E15, "globalliner")) == ("globalliner", "Global Liner Agencias")
    assert lines.leg_hours(E15, 3) == 165 / 17 and lines.departure(E15, 3) == 47 - 165 / 17
    assert lines.departure(E15, 3, 36) == 36 - 165 / 17
    elbspirit = PACK.get("dock-36A-w06x1-busy-0-e07")
    assert (elbspirit.ships[10].from_port, lines.leg_hours(elbspirit, 10), lines.departure(elbspirit, 10)) == (
        "Monrovia", None, None)
    assert Counter((s.from_port, lines.meta(t, s.id)["leg_nm"]) for t in PACK.tasks for s in t.ships
                   if s.from_port in ("Anvers", "Moerdijk", "Al 'Aqabah")) == {
        ("Anvers", 1893): 3, ("Moerdijk", 1893): 6, ("Al 'Aqabah", 1980): 1}
    assert Counter(s.from_port for t in PACK.tasks for s in t.ships if lines.meta(t, s.id)["leg_nm"] is None) == {
        "Colombo": 6, "Monrovia": 3, "Halifax": 2, "Ningbo": 2, "Montreal": 2, "Savannah": 1}
    biases = [m["bias"] for t in PACK.tasks for m in t.rules["lines"]["ships"]]
    assert max(map(abs, biases)) <= 4 and 0.75 <= sum(b > 0 for b in biases) / len(biases) <= 0.85


def test_the_published_schedule_is_the_lines_estimate_from_72_hours_out_not_the_truth():
    """Each ship arrives off its schedule by its agent's error from 72 hours out, at hour 1 at the earliest, so 72
    hours out its agent's ETA is the schedule unless the ship can't arrive that late. A delayed or bunched ship's whole
    story moves with it: it arrives after its news and later than it would have without it. An unscheduled call keeps
    v4's arrival, which its notice announces."""
    clamped = 0
    for task in PACK.tasks:
        news = lines.first_known(task)
        for s, was in zip(task.ships, WIND.get(task.task_id).ships, strict=True):
            m = lines.meta(task, s.id)
            miss = round(lines.ETA_ERROR * m["bias"] * lines.ETA_HORIZON)
            assert (m["scheduled"], m["v4_arrival"]) == (was.planned_hour, was.arrival)
            if s.id not in news:
                assert (m["before_news"], s.arrival) == (None, max(1, was.planned_hour + miss))
            elif was.planned_hour is None:
                assert (m["before_news"], s.arrival) == (None, was.arrival)
            else:
                before = max(was.planned_hour + miss, news[s.id] + 2)
                assert (m["before_news"], s.arrival) == (before, max(was.arrival + miss, before + 1))
                assert news[s.id] < before < s.arrival
            if s.id not in news and s.arrival > 1:
                far = s.arrival - lines.ETA_HORIZON
                slowest = lines.slowest(task, s.id, far, s.arrival)
                assert lines.estimate(task, s.id, far) == min(m["scheduled"], slowest)
                clamped += slowest < m["scheduled"]
    assert clamped == 18
    assert [(lines.scheduled(E15, s), lines.before_news(E15, s), E15.ships[s].arrival)
            for s in (1, 3, 5, 6, 9, 16)] == [
        (7, None, 1), (36, None, 47), (54, 63, 83), (66, 48, 54), (111, None, 89), (None, None, 69)]
    assert (lines.estimate(E15, 3, 47 - 72), lines.estimate(E15, 9, 89 - 72), lines.slowest(E15, 9, 89 - 72, 89)) == (
        36, 103, 103)


@pytest.mark.parametrize("task", WEEKS)
def test_an_eta_holds_from_72_hours_out_stays_between_the_next_hour_and_the_slowest_arrival_and_is_exact_from_the_call(
        task):
    for s in task.ships:
        errors = []
        far = s.arrival - round(lines.ETA_ERROR * lines.meta(task, s.id)["bias"] * lines.ETA_HORIZON)
        for hour in range(-120, s.arrival + 1):
            eta, slowest = lines.estimate(task, s.id, hour), lines.slowest(task, s.id, hour, s.arrival)
            assert eta == s.arrival if s.arrival - hour <= lines.CALL_LEAD else hour + 1 <= eta <= slowest
            if s.arrival - hour >= lines.ETA_HORIZON:
                assert eta == min(far, slowest)
            errors.append(abs(eta - s.arrival))
        assert errors == sorted(errors, reverse=True), s.id


def test_etas_are_mostly_early_by_a_share_of_the_hours_left():
    assert [lines.estimate(E15, 3, h) for h in (-25, 0, 23, 35, 45, 46, 47)] == [36, 40, 43, 45, 47, 47, 47]
    assert [lines.estimate(E15, 8, h) for h in (20, 44, 68, 80, 90, 91)] == [97, 96, 94, 93, 92, 92]
    assert lines.meta(E15, 8)["bias"] < 0 < lines.meta(E15, 3)["bias"]
    assert lines.estimate(E15, 3, 0, 36) == 31


@pytest.mark.parametrize("task", WEEKS)
def test_the_timetable_is_v4s_watches_each_with_the_reports_made_since_the_watch_before(task):
    v4, ours = schedule(lines.as_v4(task)), lines.timetable(task)
    hours = [w.hour for w in v4]
    assert [(w.index, w.hour, [n.event_id for n in w.notices]) for w in v4] == [
        (w.index, w.hour, [n.event_id for n in w.notices]) for w in schedule(WIND.get(task.task_id))]
    assert [(w.index, w.hour) for w in ours] == [(w.index, w.hour) for w in v4]
    for w, was in zip(ours, v4, strict=True):
        assert w.notices[:len(was.notices)] == was.notices
        assert {n.kind for n in w.notices[len(was.notices):]} <= set(lines.REPORTS)
        made = reports(w)
        assert made == sorted(made, key=lambda n: (n.hour, n.event_id))
        for n in made:
            e, s = n.event, task.ships[n.event["ship"]]
            planned = n.event_id.endswith("-plan")
            arrival = lines.before_news(task, s.id) if planned else s.arrival
            assert w.index == next(k for k, h in enumerate(hours) if h >= e["hour"])
            assert (e["type"], n.hour, n.event_hour, n.index) == (n.kind, e["hour"], arrival, -1)
            assert e["hour"] == max(arrival - e["lead"], 0)
            assert n.event_id == f"{n.kind}-{s.id}-{e['lead']}" + ("-plan" if planned else "")
            assert e["lead"] == lines.CALL_LEAD if n.kind == "call" else e["lead"] in lines.REPORT_LEADS
            assert not planned or n.kind == "eta"
            assert e["eta"] == (arrival if n.kind == "call" else lines.estimate(task, s.id, e["hour"], arrival))
            assert (n.name, n.text) == (lines.firm_name(task, lines.firm(task, s.id)), lines.report_text(task, e))


@pytest.mark.parametrize("task", WEEKS)
def test_every_ship_due_by_the_last_watch_calls_in_and_the_week_opens_with_the_latest_report_made_before_it(task):
    """A delayed or bunched ship's opening report is from the plan as it stood, when its news comes after hour 0."""
    made = [n for w in lines.timetable(task) for n in reports(w)]
    last = lines.timetable(task)[-1].hour
    assert sorted(n.event["ship"] for n in made if n.kind == "call") == [
        s.id for s in task.ships if s.arrival - lines.CALL_LEAD <= last]
    news = lines.first_known(task)
    for s in task.ships:
        opening = [n for n in made if n.event["ship"] == s.id and n.event_hour - n.event["lead"] <= 0]
        if s.id not in news:
            leads = [lead for lead in (*lines.REPORT_LEADS, lines.CALL_LEAD) if s.arrival - lead <= 0]
        elif (planned := lines.before_news(task, s.id)) is not None and news[s.id] > 0:
            leads = [lead for lead in lines.REPORT_LEADS if planned - lead <= 0]
        else:
            leads = []
        assert [n.event["lead"] for n in opening] == ([min(leads)] if leads else [])


@pytest.mark.parametrize("task", WEEKS)
def test_a_late_bunched_or_unscheduled_ship_is_reported_from_the_truth_only_after_its_news_and_from_the_plan_before(
        task):
    """first_known is the hour of the watch that brings a ship's news, and a report from the plan as it stood comes
    only at an earlier watch."""
    told, hours = news(lines.as_v4(task)), [w.hour for w in lines.timetable(task)]
    assert lines.first_known(task) == {s: hours[max(k for k, _ in notices)] for s, notices in told.items()}
    for w in lines.timetable(task):
        for n in reports(w):
            if (s := n.event["ship"]) in told:
                k = max(k for k, _ in told[s])
                if n.event_id.endswith("-plan"):
                    assert w.index < k and lines.before_news(task, s) is not None
                else:
                    assert n.hour > lines.first_known(task)[s] and w.index > k


def test_the_reports_of_one_week_watch_by_watch():
    watches = lines.timetable(E15)
    assert [(w.hour, [n.event_id for n in reports(w)]) for w in watches] == [
        (0, ["call-0-1", "call-1-1", "eta-2-48", "eta-3-48", "eta-6-48-plan"]),
        (24, ["eta-2-24", "eta-4-48", "eta-5-48-plan", "eta-3-24", "call-2-1", "eta-6-24-plan"]),
        (30, ["eta-4-24"]),
        (42, ["eta-5-48", "eta-7-48", "eta-9-48"]),
        (72, ["eta-8-48", "eta-16-24", "call-3-1", "call-4-1", "call-6-1", "eta-5-24", "eta-7-24", "eta-9-24",
              "call-16-1", "eta-8-24"]),
        (96, ["eta-10-48", "call-5-1", "eta-11-48", "call-7-1", "call-9-1", "call-8-1", "eta-12-48"])]
    assert news(lines.as_v4(E15)) == {5: [(2, 30)], 6: [(3, 42)], 16: [(3, 45)]}
    assert lines.first_known(E15) == {5: 30, 6: 42, 16: 42}
    opening = reports(watches[0])
    assert [(n.name, n.text) for n in (opening[0], opening[3])] == [
        ("A. Pérez y Cía", "PERSEUS (ship 0) calls in: at buoy S, arriving hour 1 (Mon 01:00)."),
        ("Global Liner Agencias", "STEEN (ship 3): ETA Tue 16:00 (hour 40), as of Mon 00:00.")]
    assert reports(watches[1])[3].text == "STEEN (ship 3): ETA Tue 19:00 (hour 43), as of Mon 23:00."
    assert (opening[4].event_hour, opening[4].event) == (
        48, {"type": "eta", "ship": 6, "hour": 0, "lead": 48, "eta": 60})
    assert opening[4].text == "ONE FREEDOM (ship 6): ETA Wed 12:00 (hour 60), as of Mon 00:00."
