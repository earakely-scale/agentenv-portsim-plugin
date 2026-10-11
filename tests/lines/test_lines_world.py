"""The lines week (agentenv_portsim.lines.LinesWeek): the arrivals as known (published, then each ETA its agent gives,
then the agreed or called-in arrival), the agents' answers to the planner's asks and requests, an agreed ship's news
given as the agreement, and whole weeks played in process keeping their audit."""

import json
from collections.abc import Iterator
from dataclasses import replace

import pytest
from berth_core import Task, plan_to_list

from agentenv_portsim import lines, marine, wind, world
from agentenv_portsim.lines import LinesWeek
from agentenv_portsim.schedule import label

PACK = lines.pack()
E15 = PACK.get("dock-24B-w06x1-busy-0-e15")
WEEKS = [pytest.param(t, id=t.task_id) for t in PACK.tasks]


def walk(task: Task, policy: world.Policy | None = None) -> Iterator[LinesWeek]:
    """The week at each of its watches, its news delivered, confirming ``policy``'s plan before moving on."""
    week = LinesWeek(task)
    while True:
        yield week
        if policy:
            target = policy(week)
            if rows := [r for r in plan_to_list(target) if week.plan.get(r["ship"]) != target[r["ship"]]]:
                week.confirm(rows)
        if week.last:
            return
        week.open()
        for n in week.watches[week.watch].notices:
            week.notice(n.event_id, n.name, n.text, "trigger")


def arrival(week: LinesWeek, sid: int) -> int:
    return next(s.arrival for s in week.view.ships if s.id == sid)


def turn(week: LinesWeek, sid: int) -> int:
    return week.view.rules["lines"]["turns"][sid]


def row(week: LinesWeek, sid: int) -> str:
    return next(line for line in lines.section(week).splitlines() if line.startswith(f"- ship {sid} "))


def test_a_late_ship_shows_its_published_arrival_then_each_eta_it_is_given_then_its_arrival_once_it_calls_in():
    nanto, seen = E15.ships[5], []
    for week in walk(E15):
        seen.append((week.hour, arrival(week, 5), turn(week, 5), week.told.get(5), 5 in week.arrived))
    assert (nanto.planned_hour, nanto.arrival) == (54, 74)
    assert seen == [(0, 54, 54, None, False), (24, 54, 54, None, False), (30, 68, 68, (30, 68), False),
                    (42, 68, 68, (30, 68), False), (72, 71, 71, (50, 71), False), (96, 74, 74, (73, 74), True)]
    assert next(e for e in E15.disruptions if e.get("ship") == 5) == {"type": "late", "ship": 5, "hours": 20, "eta": 68}


@pytest.mark.parametrize("task", WEEKS)
def test_the_week_as_known_holds_the_agreed_or_called_in_arrival_else_the_latest_eta_else_the_published_one(task):
    for week in walk(task, world.naive):
        view = week.view
        assert [s.id for s in view.ships] == [s.id for s in wind.known(task, week.revealed).ships]
        for s in view.ships:
            settled = s.id in week.locks or s.id in week.arrived
            known = week.actual(s.id) if settled else week.told[s.id][1] if s.id in week.told else (
                task.ships[s.id].planned_hour)
            assert (s.arrival, view.rules["lines"]["turns"][s.id]) == (
                known, task.ships[s.id].arrival if settled else known)
        called = {week.scheduled[e["event_id"]].event["ship"] for e in week.log if e["kind"] == "call"}
        assert week.arrived == called


def test_until_its_agents_next_report_a_late_ships_true_arrival_never_reaches_the_planner():
    """The late ship arriving two hours later still: what the planner sees is byte for byte the same until the agent's
    24-hour report, the first word that comes from the truth."""
    later = replace(E15, ships=[replace(s, arrival=76) if s.id == 5 else s for s in E15.ships], disruptions=[
        e | {"hours": 22} if e.get("ship") == 5 and e["type"] == "late" else e for e in E15.disruptions])
    seen = []
    for task in (E15, later):
        out = []
        for week in walk(task, world.naive):
            out.append(json.dumps([week.situation(), week.check(plan_to_list(world.naive(week))),
                                   lines.step_lines(week), week.messages], ensure_ascii=False))
        seen.append(out)
    assert [w.hour for w in lines.timetable(E15)] == [0, 24, 30, 42, 72, 96]
    assert seen[0][:4] == seen[1][:4] and seen[0][4] != seen[1][4]


def test_get_situation_ends_with_the_agents_and_the_arrivals_as_known():
    week = LinesWeek(E15)
    situation = week.situation()["situation"]
    view = week.view
    assert situation.endswith("\n\n".join(["", marine.section(view), wind.section(view), lines.section(week)]))
    section = lines.section(week).splitlines()
    assert section[0] == "## Arrivals and the ships' agents" and section[7] == "- Arrivals as known now:"
    assert section[3] == ("- A ship can't berth before it arrives: a window that starts earlier begins when the ship "
                          "gets in, or once the wind lets it move.")
    assert section[6] == (
        "- Agents, and their ships: A. Pérez y Cía (aperez): ships 0, 1, 12, 15; Boluda Lines (boluda): ships 7; "
        "CMA CGM Ibérica (cmacgm): ships 2, 11; COSCO Shipping Lines Spain (cosco): ships 4; Global Liner Agencias "
        "(globalliner): ships 3; Hapag-Lloyd Spain (hapag): ships 8, 9; Noatum Maritime (noatum): ships 5, 10, 13, "
        "14; Ocean Network Express Spain (one): ships 6.")
    assert [row(week, s) for s in (0, 3, 5)] == [
        "- ship 0 PERSEUS: arrival hour 0, arrived hour 0, turn 0; from Algeciras",
        "- ship 3 STEEN: arrival hour 31, ETA hour 31, as of Mon 00:00; from Valencia",
        "- ship 5 NANTO: arrival hour 54, published schedule; from Alicante"]
    assert len(section) == 8 + len(view.ships) and "16" not in section[6]


def test_a_ship_that_has_called_in_but_not_yet_arrived_reads_as_arriving():
    [(hour, sid)] = [(w.hour, n.event["ship"]) for w in lines.timetable(E15) for n in w.notices
                     if n.kind == "call" and n.event["eta"] > w.hour]
    week = next(w for w in walk(E15) if w.hour == hour)
    ship = E15.ships[sid]
    assert sid in week.arrived and week.actual(sid) == ship.arrival == hour + 1
    assert row(week, sid) == (f"- ship {sid} {ship.name}: arrival hour {ship.arrival}, called in, arriving hour "
                              f"{ship.arrival}, turn {ship.arrival}; from {ship.from_port}")
    assert week.status(lines.firm(E15, sid), sid) == {"ship": sid, "name": ship.name, "eta": ship.arrival,
                                                      "as_of": hour}
    assert row(week, 0) == "- ship 0 PERSEUS: arrival hour 0, arrived hour 0, turn 0; from Algeciras"


def test_an_agent_agrees_an_arrival_the_ship_can_make_and_says_why_it_cannot_otherwise():
    week = LinesWeek(E15)
    assert week.reach(3, 0) == (36, 42)
    assert week.request("globalliner", 3, 35) == {"ship": 3, "name": "STEEN", "agreed": False, "eta": 31,
                                                   "reason": "can't arrive that early"}
    assert week.request("globalliner", 3, 43) == {"ship": 3, "name": "STEEN", "agreed": False, "eta": 31,
                                                   "reason": "can't slow down that much"}
    assert week.locks == {} and week.told[3] == (0, 31)
    assert week.request("globalliner", 3, 42) == {"ship": 3, "name": "STEEN", "agreed": True, "arrival": 42,
                                                   "turn": 36, "slowing": True}
    assert week.request("globalliner", 3, 36)["slowing"] is False and week.actual(3) == 36
    assert week.request("globalliner", 3, 42)["agreed"]
    assert week.locks[3] == pytest.approx((36 - 165 / 17, 165 / 17, 42))
    truth = week.truth()
    assert (truth.ships[3].arrival, truth.rules["lines"]["turns"][3], E15.ships[3].arrival) == (42, 36, 36)
    assert (arrival(week, 3), turn(week, 3), week.told[3]) == (42, 36, (0, 42))
    assert row(week, 3) == "- ship 3 STEEN: arrival hour 42, agreed hour 42, turn 36; from Valencia"
    assert week.request("globalliner", 3, 50) == {"ship": 3, "name": "STEEN", "agreed": False, "eta": 42,
                                                   "reason": "can't slow down that much"}
    assert week.status("globalliner", 3) == {"ship": 3, "name": "STEEN", "eta": 42, "agreed": True, "turn": 36}


def test_a_ship_still_in_its_previous_port_can_slow_only_by_seven_tenths_of_its_leg():
    """STEEN sails the 165 nm from Valencia in under ten hours: until it leaves, the most it can give is 0.7 of that
    leg; once at sea, 0.7 of the hours left. A ship from beyond the week's reach can stretch all its hours."""
    week, leg = LinesWeek(E15), 165 / 17
    assert lines.departure(E15, 3) == 36 - leg > 26
    assert week.reach(3, 0) == week.reach(3, 26) == (36, int(36 + 0.7 * leg)) == (36, 42)
    assert week.reach(3, 30) == (36, int(30 + 6 * 1.7)) == (36, 40)
    assert week.reach(3, 35) == (36, 36)
    assert week.remaining(3, 0) == pytest.approx((36 - leg, leg)) and week.remaining(3, 30) == (30, 6)
    assert lines.departure(E15, 6) < 0 and week.reach(6, 0) == (72, int(72 * 1.7)) == (72, 122)
    elbspirit = PACK.get("dock-36A-w06x1-busy-0-e07")
    assert LinesWeek(elbspirit).reach(10, 0) == (85, 144)


def test_a_slowed_ship_can_change_pace_again_only_within_what_it_has_left():
    week = LinesWeek(E15)
    week.request("globalliner", 3, 42)
    left = (165 / 17) * (42 - 30) / (42 - (36 - 165 / 17))
    assert week.remaining(3, 30) == pytest.approx((30, left))
    assert week.reach(3, 30) == (38, int(30 + left * 1.7)) == (38, 42)


def test_an_agent_answers_only_for_its_own_ships_that_the_week_shows():
    week = LinesWeek(E15)
    for args, message in [(("aperez", 3), "ship 3 STEEN is not this agent's: Global Liner Agencias handles it"),
                          (("hapag", 16), "no ship 16 in the week"), (("globalliner", "3"), "no ship '3' in the week"),
                          (("aperez", True), "no ship True in the week"), (("aperez", 99), "no ship 99 in the week")]:
        for ask in (week.status, lambda firm, sid: week.request(firm, sid, 40)):
            with pytest.raises(ValueError, match=f"^{message}$"):
                ask(*args)
    for bad in (40.0, "40", True):
        with pytest.raises(ValueError, match="^request_arrival must be an hour"):
            week.request("globalliner", 3, bad)
    assert week.exchanges == [] and week.locks == {}


def test_status_records_the_eta_it_tells_and_an_arrived_ship_reports_its_arrival():
    week = LinesWeek(E15)
    assert (arrival(week, 7), row(week, 7)) == (84, "- ship 7 VERONICA B: arrival hour 84, published schedule; from "
                                                     "Alicante")
    assert week.status("boluda", 7) == {"ship": 7, "name": "VERONICA B", "eta": 78, "as_of": 0}
    assert (week.told[7], arrival(week, 7), turn(week, 7)) == ((0, 78), 78, 78)
    assert row(week, 7) == "- ship 7 VERONICA B: arrival hour 78, ETA hour 78, as of Mon 00:00; from Alicante"
    assert week.status("aperez", 0) == {"ship": 0, "name": "PERSEUS", "arrived": 0, "turn": 0}
    assert week.request("aperez", 0, 1) == {"ship": 0, "name": "PERSEUS", "agreed": False,
                                            "reason": "already arrived at hour 0"}
    assert week.exchanges == [
        {"watch": 0, "hour": 0, "firm": "boluda", "ship": 7, "ask": "eta", "call": 0,
         "reply": {"ship": 7, "name": "VERONICA B", "eta": 78, "as_of": 0}},
        {"watch": 0, "hour": 0, "firm": "aperez", "ship": 0, "ask": "eta", "call": 0,
         "reply": {"ship": 0, "name": "PERSEUS", "arrived": 0, "turn": 0}},
        {"watch": 0, "hour": 0, "firm": "aperez", "ship": 0, "ask": "request_arrival", "arrival": 1, "call": 0,
         "reply": {"ship": 0, "name": "PERSEUS", "agreed": False, "reason": "already arrived at hour 0"}}]


def test_the_latest_eta_stands_whether_the_planner_asked_for_it_or_the_agent_reported_it():
    week = next(w for w in walk(E15) if w.hour == 42)
    assert week.status("boluda", 7) == {"ship": 7, "name": "VERONICA B", "eta": 81, "as_of": 42}
    week.open()
    report = next(n for n in week.watches[week.watch].notices if n.event_id == "eta-7-24")
    for n in week.watches[week.watch].notices:
        week.notice(n.event_id, n.name, n.text, "trigger")
    assert (report.event["hour"], report.event["eta"], week.told[7]) == (60, 82, (60, 82))
    assert week.status("boluda", 7)["eta"] == 83 and (week.told[7], arrival(week, 7)) == ((72, 83), 83)


@pytest.mark.parametrize("task", WEEKS)
def test_a_whole_week_played_keeps_its_audit_and_reports_its_lines(task):
    week = world.play(task, world.naive, week=LinesWeek)
    assert week.audit() == {"ok": True, "problems": []}
    data = week.data()
    assert data["lines"]["exchanges"] == [] and data["lines"]["agreed"] == []
    assert data["lines"]["arrivals"] == [{"ship": s.id, "arrival": s.arrival, "turn": s.arrival} for s in task.ships]
    assert data["audit"] == week.audit() and data["grade"] == week.grade


def test_the_audit_holds_no_report_to_a_lead_but_every_other_notice_still_to_its_own():
    class Timed(LinesWeek):
        untimed = ()

    problems = world.play(E15, world.naive, week=Timed).audit()["problems"]
    assert problems[:2] == ["call-1-1: revealed -17 h ahead at hour 24", "call-2-1: revealed 0 h ahead at hour 24"]
    assert {p.split("-")[0] for p in problems} == set(lines.REPORTS)
    assert world.play(E15, world.naive, week=LinesWeek).audit() == {"ok": True, "problems": []}


def test_agreeing_an_arrival_then_playing_on_keeps_the_audit_and_the_agreement():
    def policy(week: LinesWeek):
        if week.watch == 0:
            week.request("globalliner", 3, 42)
            week.request("noatum", 5, 90)
        return world.naive(week)

    week = world.play(E15, policy, week=LinesWeek)
    assert week.audit() == {"ok": True, "problems": []}
    assert week.plan[3][0] >= 42 and week.truth().ships[3].arrival == 42
    data = week.data()["lines"]
    assert data["agreed"] == [{"ship": 3, "arrival": 42, "turn": 36}]
    assert [(e["watch"], e["firm"], e["ship"], e["arrival"], e["reply"]["agreed"]) for e in data["exchanges"]] == [
        (0, "globalliner", 3, 42, True), (0, "noatum", 5, 90, False)]
    assert data["exchanges"][1]["reply"] == {"ship": 5, "name": "NANTO", "agreed": False,
                                             "eta": lines.estimate(E15, 5, 0), "reason": "can't slow down that much"}
    assert data["arrivals"][3] == {"ship": 3, "arrival": 42, "turn": 36}
    assert [a for a in data["arrivals"] if a["ship"] != 3] == [
        {"ship": s.id, "arrival": s.arrival, "turn": s.arrival} for s in E15.ships if s.id != 3]


def agreeing(*requests: tuple[str, int, int]) -> world.Policy:
    """Naive, after agreeing ``requests`` (firm, ship, arrival) at watch 0."""
    def policy(week: LinesWeek):
        if week.watch == 0:
            for firm, sid, at in requests:
                assert week.request(firm, sid, at)["agreed"]
        return world.naive(week)
    return policy


def test_an_agreed_ships_reports_and_news_reach_the_planner_as_the_agreement():
    """STEEN's 24-hour report and call, and NANTO's delay notice, reports and call, all come as the arrival agreed;
    the log keeps the scheduled notices, so the audit holds, and a call no longer marks an agreed ship arrived."""
    week = world.play(E15, agreeing(("globalliner", 3, 42), ("noatum", 5, 76)), week=LinesWeek)
    steen = "STEEN (ship 3): arriving hour 42 (Tue 18:00), as agreed; turn hour 36."
    nanto = f"NANTO (ship 5): arriving hour 76 ({label(76)}), as agreed; turn hour 74."
    about = [(m["hour"], m["from"], m["text"]) for m in week.messages if "(ship 3)" in m["text"] or
             "(ship 5)" in m["text"] or "Ship 5 " in m["text"]]
    assert about == [(24, "Global Liner Agencias", steen), (30, "NANTO", nanto), (42, "Global Liner Agencias", steen),
                     (72, "Noatum Maritime", nanto), (96, "Noatum Maritime", nanto)]
    delivered = [e["event_id"] for e in week.log if e["via"] == "trigger" and
                 week.scheduled[e["event_id"]].event.get("ship") in (3, 5)]
    assert delivered == ["eta-3-24", "late-3", "call-3-1", "eta-5-24", "call-5-1"]
    assert all(e["matches"] for e in week.log) and week.audit() == {"ok": True, "problems": []}
    assert week.arrived.isdisjoint({3, 5}) and (week.told[3], week.told[5]) == ((0, 42), (0, 76))
    assert [row(week, s) for s in (3, 5)] == [
        "- ship 3 STEEN: arrival hour 42, agreed hour 42, turn 36; from Valencia",
        "- ship 5 NANTO: arrival hour 76, agreed hour 76, turn 74; from Alicante"]


def test_other_ships_reports_keep_their_scheduled_text():
    agreed = world.play(E15, agreeing(("globalliner", 3, 42)), week=LinesWeek)
    plain = world.play(E15, world.naive, week=LinesWeek)
    assert [m for m in agreed.messages if "(ship 3)" not in m["text"]] == [
        m for m in plain.messages if "(ship 3)" not in m["text"]]
    assert [m["text"] for m in plain.messages if m["text"].startswith("STEEN (ship 3)")] == [
        n.text for n in plain.scheduled.values() if n.event_id in ("eta-3-24", "call-3-1")]


def test_a_bunching_notice_with_one_ship_agreed_still_gives_the_others_news():
    task = PACK.get("dock-24B-w07x1-busy-0-e04")
    bunching = next(e for e in task.disruptions if e["type"] == "bunching")
    first, *others = bunching["ships"]
    week = world.play(task, agreeing((lines.firm(task, first), first, task.ships[first].arrival)), week=LinesWeek)
    [message] = [m for m in week.messages if m["from"] == "Ship agents"]
    assert all(f"ship {s}" in message["text"] for s in others), message


def test_asking_an_agent_answers_from_the_truth_even_before_the_news_of_a_delay():
    """By design: the agent knows its ship, so asking about NANTO at hour 0 gives its current ETA well before the delay
    notice at hour 30, which then supersedes it."""
    published, eta = E15.ships[5].planned_hour, lines.estimate(E15, 5, 0)
    notice = next(e for e in E15.disruptions if e.get("ship") == 5)
    assert lines.first_known(E15)[5] == 30 and published < eta < notice["eta"]
    for week in walk(E15):
        if week.hour == 0:
            assert arrival(week, 5) == published
            assert week.status("noatum", 5) == {"ship": 5, "name": "NANTO", "eta": eta, "as_of": 0}
            assert week.request("noatum", 5, published)["reason"] == "can't arrive that early"
            assert arrival(week, 5) == eta
        elif week.hour == 30:
            assert (week.told[5], arrival(week, 5)) == ((30, notice["eta"]), notice["eta"])
            break


def test_the_notices_list_adds_the_agreement_to_an_agreed_late_ships_delay_notice():
    """The situation's notices keep the delay text and add the agreed arrival after it."""
    week = LinesWeek(E15)
    [late] = [i for i, e in enumerate(E15.disruptions) if e["type"] == "late" and e["ship"] == 5]
    reach = week.reach(5, week.hour)
    assert week.request(lines.firm(E15, 5), 5, reach[0] + 2)["agreed"]
    week.revealed.append(f"late-{late}")
    [text] = [t for e, t in zip(week.view.disruptions, week.view.notices, strict=True)
              if e["type"] == "late" and e["ship"] == 5]
    assert text == E15.notices[late] + " Since then: " + week.agreement(5)
