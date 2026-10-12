"""The viewer on a real lines week (lines_recorded.py): replayed through a LinesWeek against the lines pack and
references, each message to a ship's agent played on the week in its place among the calls and kept as a step with the
replies the planner got, every step with the lines as step_lines gives them, the explorer's lines week, v1 to v4 with no
lines state, v5 heading the overview, and (with Chrome and the network) the panel's exchanges and agreed arrivals, a
slowed ship waiting at sea until its agreed hour, and the overview's v5 board."""

import json
import re
import shutil

import pytest
from lines_recorded import E2E_RUN, LINES_ROOT, SONNET
from recorded import LIVE, MARINE_ROOT, MARINE_RUN, MARINE_TASK, ROOT, WIND_ROOT, WIND_RUN, WIND_TASK
from test_marine_viewer import opened
from wind_fixtures import use

from agentenv_portsim import lines, record
from agentenv_portsim.episodes import MESSAGE_TOOL, ReplayError, Runs, env, week_of
from agentenv_portsim.lines import LinesWeek
from agentenv_portsim.schedule import LINES_ENV
from agentenv_portsim.sweep import Sweep, results
from agentenv_portsim.view import EXT, route

[ROW] = results(LINES_ROOT / E2E_RUN)
LINES_TASK = ROW["task_id"]
TASK = lines.pack().get(LINES_TASK)
REF = next(r for r in lines.references() if r["task_id"] == LINES_TASK)
EPISODE = (E2E_RUN, SONNET, LINES_TASK)
STEPS = ("check_plan", "confirm_berths", "advance")
FAILED = "An unexpected framework error occurred. Correlation ID: 633d1bde5c544e36a1ce0a28f05dd2f7"
PANEL = '[...document.querySelectorAll(".ps-lines, .ps-exch li")].map((e) => e.innerText)'


@pytest.fixture(scope="module")
def lines_runs() -> Runs:
    return Runs(LINES_ROOT)


@pytest.fixture(scope="module")
def rollout(lines_runs) -> dict:
    return lines_runs.rollout(*EPISODE)


def recorded() -> dict:
    return json.loads((LINES_ROOT / E2E_RUN / ROW["transcript"]).read_text())


def slowed(rollout: dict) -> int:
    """The first ship the week slowed at the planner's request."""
    return next(e["ship"] for e in rollout["live"]["lines"]["exchanges"] if e["reply"].get("slowing"))


def own(steps: list[dict], k: int) -> list[dict]:
    """The exchanges step k made: those its watch has beyond the step before it in the same watch."""
    before = steps[k - 1]["lines"]["exchanges"] if k and steps[k - 1]["watch"] == steps[k]["watch"] else []
    return steps[k]["lines"]["exchanges"][len(before):]


def answered(e: dict) -> dict:
    """An exchange's reply as portsim-line passes it on."""
    if e["ask"] == "eta":
        return e["reply"] | ({"agreed_before": True} if e["reply"].get("agreed") else {})
    return e["reply"] | {"asked": e["arrival"]}


def through_watch(msgs: list[dict], i: int) -> int:
    """The end of the watch message i is in: just past the result of the next advance."""
    return next(j for j in range(i, len(msgs)) if msgs[j]["role"] == "tool" and msgs[j]["name"] == "advance") + 1


def basis(ship: int, watch: int) -> int:
    """The arrival the ship's agent works from at the watch: the plan as it stood until its news, then the truth."""
    pending = REF["watch_hours"][watch] < lines.first_known(TASK).get(ship, 0)
    return lines.before_news(TASK, ship) if pending else TASK.ships[ship].arrival


def played(policy: dict) -> dict:
    return {k: v for k, v in policy.items() if k not in ("plans", "configs", "exchanges")}


def agreeing(msgs: list[dict], ship: int) -> tuple[int, int]:
    """The assistant message and the tool result of the first message an agent agreed for the ship."""
    i = next(i for i, m in enumerate(msgs) if m.get("name") == MESSAGE_TOOL and any(
        r["ship"] == ship and r.get("agreed") is True for r in json.loads(m["content"])["replies"]))
    a = next(a for a in range(i, -1, -1) if msgs[a]["role"] == "assistant"
             and any(c["id"] == msgs[i]["tool_call_id"] for c in msgs[a]["tool_calls"]))
    return a, i


def test_the_run_is_a_lines_sweep_played_on_portsim_lines():
    spec = Sweep(**json.loads((LINES_ROOT / E2E_RUN / "sweep.json").read_text()))
    assert spec == Sweep(E2E_RUN, [SONNET], [LINES_TASK], 1, 5.0, live=True, lines=True)
    assert (env(spec), week_of(spec)) == (LINES_ENV, LinesWeek)


def test_a_lines_replay_gives_back_every_recorded_step_and_the_runs_grade(rollout):
    scored, rec = ROW, recorded()
    planned = [s for s in rollout["steps"] if s["tool"] in STEPS]
    assert [(s["turn"], s["tool"], s["entries"]) for s in planned] == [
        (s["turn"], s["tool"], s["plan"]) for s in rec["steps"]]
    assert [{k: v for k, v in s["result"].items() if k != "violations"} for s in planned] == [
        s["result"] for s in rec["steps"]]
    grade = rollout["final"]["grade"]
    assert rollout["reward"] == grade["reward"] == scored["reward"] == rec["reward"]
    assert (grade["cost"], grade["excused_cost"], grade["regret"], grade["anchor_hours"]) == (
        scored["plan_cost"], scored["excused_cost"], scored["regret"], scored["anchor_hours"])
    assert len(rollout["live"]["lines"]["exchanges"]) == scored["messages"]
    assert rollout["live"]["audit"] == {"ok": True, "problems": []}
    assert (rollout["live"]["end_reason"], rollout["final"]["submitted"]) == ("done", True)
    assert [w["hour"] for w in rollout["live"]["watches"]] == REF["watch_hours"]


def test_the_bulletins_leave_out_what_the_week_did_not_deliver(rollout):
    """A repeat in one bulletin, and a report or call about an agreed ship once its agreed hour has come, reach no
    one: NAVIOS INDIGO, agreed for 6, calls in by the bulletin at 24, where CMA CGM DALILA's call repeats its 24-hour
    report as the agreement; STEEN, agreed for 47, calls in by the bulletin at 72. ONE FREEDOM's agreement for 67,
    made before its news, stands, and the news gives that hour."""
    shown = {b["event_id"]: b["text"] for b in rollout["live"]["bulletins"]}
    assert [(n.event_id, w.hour) for w in lines.timetable(TASK) for n in w.notices if n.event_id not in shown] == [
        ("call-1-1", 24), ("call-2-1", 24), ("eta-16-24", 72), ("call-3-1", 72), ("call-4-1", 72), ("call-6-1", 72),
        ("call-16-1", 72), ("call-5-1", 96), ("call-7-1", 96), ("call-9-1", 96)]
    assert shown["late-4"] == TASK.notices[4].replace("ETA hour 56", "ETA hour 67") + (
        " The earlier agreement stands: ONE FREEDOM (ship 6): arriving hour 67 (Wed 19:00), as agreed; turn hour 54.")


def test_the_end_to_end_week_plays_the_follower_and_scores_its_reference(rollout):
    grade = rollout["final"]["grade"]
    assert (rollout["reward"], grade["cost"], grade["anchor_hours"]) == (
        REF["rolling"]["reward"], REF["rolling"]["cost"], REF["rolling"]["anchor_hours"])
    assert [(e["watch"], e["ship"], e["arrival"]) for e in rollout["live"]["lines"]["exchanges"]] == [
        (e["watch"], e["ship"], e["arrival"]) for e in REF["rolling"]["exchanges"]]


def test_each_message_is_a_step_with_the_replies_the_planner_got(rollout):
    calls = {c["id"]: c for m in recorded()["messages"] if m["role"] == "assistant" for c in m.get("tool_calls") or []}
    sent = [(calls[m["tool_call_id"]], json.loads(m["content"])) for m in recorded()["messages"]
            if m["role"] == "tool" and m["name"] == MESSAGE_TOOL]
    steps = [(k, s) for k, s in enumerate(rollout["steps"]) if s["tool"] == MESSAGE_TOOL]
    assert [(s["call_id"], s["entries"], s["result"]) for _, s in steps] == [
        (call["id"], json.loads(call["arguments"])["requests"], got) for call, got in sent]
    for k, s in steps:
        made = own(rollout["steps"], k)
        assert all(e["firm"] == s["result"]["agent"] and e["watch"] == s["watch"] for e in made)
        assert [answered(e) for e in made] == s["result"]["replies"]
    assert sum(len(own(rollout["steps"], k)) for k, _ in steps) == len(rollout["live"]["lines"]["exchanges"])


def test_each_step_carries_this_watchs_exchanges_and_the_arrivals_agreed_so_far(rollout):
    """An agreement leaves the list only when the ship's news undoes it, and none does here: ONE FREEDOM's hour 67,
    made before its news, stands."""
    agreed: set[int] = set()
    lapsed = []
    for step in rollout["steps"]:
        known = {s["id"]: s["arrival"] for s in step["task"]["ships"]}
        assert all(e["watch"] == step["watch"] for e in step["lines"]["exchanges"])
        lapsed += [(step["watch"], s) for s in agreed - {a["ship"] for a in step["lines"]["agreed"]}]
        agreed = {a["ship"] for a in step["lines"]["agreed"]}
        assert all(known[a["ship"]] == a["arrival"] for a in step["lines"]["agreed"])
        assert [(a["ship"], a["arrival"]) for a in step["lines"]["arrivals"]] == list(known.items())
        assert all(a["known"] for a in step["lines"]["arrivals"] if a["ship"] in agreed)
    assert {a["ship"]: a["arrival"] for a in rollout["steps"][-1]["lines"]["agreed"]} == {
        e["ship"]: e["arrival"] for e in rollout["live"]["lines"]["exchanges"]
        if e["ask"] == "request_arrival" and e["reply"].get("agreed") is True}
    assert lapsed == [] and lines.first_known(TASK)[6] == REF["watch_hours"][3]
    assert [(e["watch"], e["arrival"]) for e in rollout["live"]["lines"]["exchanges"]
            if e["ship"] == 6 and e["reply"]["agreed"]] == [(0, 67)]


def test_the_end_to_end_week_slows_ships_that_keep_their_turns(rollout):
    """A turn is the arrival the ship's agent works from: ONE FREEDOM's, agreed before its news, was 48."""
    final, exchanges = rollout["steps"][-1]["lines"]["agreed"], rollout["live"]["lines"]["exchanges"]
    slowed = {a["ship"] for a in final if a["arrival"] > TASK.ships[a["ship"]].arrival}
    turns = [(e["ship"], e["reply"]["turn"]) for e in exchanges if e["ship"] in slowed and e["reply"]["agreed"]]
    assert slowed and turns == [(e["ship"], basis(e["ship"], e["watch"])) for e in exchanges
                                if e["ship"] in slowed and e["reply"]["agreed"]]
    assert [t for s, t in turns if s == 6] == [48] and basis(6, 3) == 54


def test_a_reply_the_week_does_not_give_back_stops_the_replay(lines_runs, rollout):
    msgs = recorded()["messages"]
    _, i = agreeing(msgs, slowed(rollout))
    tampered = [*msgs[:i], msgs[i] | {"content": msgs[i]["content"].replace('"agreed": true', '"agreed": false', 1)},
                *msgs[i + 1:]]
    with pytest.raises(ReplayError, match=MESSAGE_TOOL):
        lines_runs.live(TASK, tampered, LinesWeek)


def test_a_message_that_never_reached_the_env_leaves_the_week_as_it_was(lines_runs, rollout):
    msgs = recorded()["messages"]
    i = next(i for i, m in enumerate(msgs) if m["role"] == "assistant" and m.get("tool_calls"))
    refused = [{"role": "assistant", "content": "", "tool_calls": [
        {"id": "nobody", "name": MESSAGE_TOOL, "arguments": json.dumps({"agent": "nobody", "requests": [
            {"ship": 3, "request_arrival": 40}]})},
        {"id": "silent", "name": MESSAGE_TOOL, "arguments": json.dumps({"agent": "globalliner", "requests": [
            {"ship": 3, "request_arrival": 40}]})}]},
        {"role": "tool", "tool_call_id": "nobody", "name": MESSAGE_TOOL,
         "content": json.dumps({"error": "no agent 'nobody': message one of aperez, boluda"})},
        {"role": "tool", "tool_call_id": "silent", "name": MESSAGE_TOOL,
         "content": json.dumps({"error": "the agent globalliner didn't answer: ReadTimeout"})}]
    steps = [{k: v for k, v in s.items() if k != "turn"} for s in lines_runs.live(
        TASK, [*msgs[:i], *refused, *msgs[i:through_watch(msgs, i)]], LinesWeek)["steps"]]
    assert steps == [{k: v for k, v in s.items() if k != "turn"} for s in rollout["steps"][:len(steps)]]
    assert steps[-1]["tool"] == "advance"


def test_an_agent_that_failed_after_asking_the_env_leaves_its_requests_in_the_week(lines_runs, rollout):
    msgs = recorded()["messages"]
    a, i = agreeing(msgs, slowed(rollout))
    agent = json.loads(msgs[i]["content"])["agent"]
    end = through_watch(msgs, i)
    failed = [*msgs[:i], msgs[i] | {"content": json.dumps({"agent": agent, "replies": [], "text": FAILED})},
              *msgs[i + 1:end]]
    steps = lines_runs.live(TASK, failed, LinesWeek)["steps"]
    k = next(k for k, s in enumerate(steps) if s["call_id"] == msgs[i]["tool_call_id"])
    assert steps[k]["result"]["replies"] == [] and own(steps, k) == own(rollout["steps"], k)
    assert [s["lines"] for s in steps] == [s["lines"] for s in rollout["steps"][:len(steps)]]
    assert steps[-1]["tool"] == "advance"
    unsent = [*msgs[:i], *msgs[i + 1:end]]
    unsent[a] = msgs[a] | {"tool_calls": [c for c in msgs[a]["tool_calls"] if c["id"] != msgs[i]["tool_call_id"]]}
    with pytest.raises(ReplayError):
        lines_runs.live(TASK, unsent, LinesWeek)


def test_an_eta_query_and_another_firms_ship_replay_as_the_agent_answers(lines_runs, rollout):
    ship, msgs = slowed(rollout), recorded()["messages"]
    a, i = agreeing(msgs, ship)
    agent = json.loads(msgs[i]["content"])["agent"]
    agreed = next(r["arrival"] for r in json.loads(msgs[i]["content"])["replies"] if r["ship"] == ship)
    other = next(s.id for s in TASK.ships if lines.firm(TASK, s.id) != agent)
    query = {"id": "query", "name": MESSAGE_TOOL, "arguments": json.dumps(
        {"agent": agent, "requests": [{"ship": ship, "ask": "eta"}, {"ship": other, "ask": "eta"}]})}
    reply = {"ship": ship, "name": TASK.ships[ship].name, "eta": agreed, "agreed": True,
             "turn": next(r["turn"] for r in json.loads(msgs[i]["content"])["replies"] if r["ship"] == ship)}

    def asked(eta: int) -> list[dict]:
        replies = [reply | {"eta": eta, "agreed_before": True},
                   {"error": f"Error calling tool 'ship_status': ship {other} {TASK.ships[other].name} is not this "
                             f"agent's: {lines.firm_name(TASK, lines.firm(TASK, other))} handles it"}]
        return [*msgs[:a], msgs[a] | {"tool_calls": [*msgs[a]["tool_calls"], query]}, *msgs[a + 1:i + 1],
                {"role": "tool", "tool_call_id": "query", "name": MESSAGE_TOOL,
                 "content": json.dumps({"agent": agent, "replies": replies, "text": ""})}]

    steps = lines_runs.live(TASK, asked(agreed), LinesWeek)["steps"]
    k = next(k for k, s in enumerate(steps) if s["call_id"] == "query")
    assert [e["reply"] for e in own(steps, k)] == [reply]
    with pytest.raises(ReplayError, match="query"):
        lines_runs.live(TASK, asked(agreed + 1), LinesWeek)


def test_a_lines_run_is_listed_on_portsim_lines_with_the_lines_references(lines_runs, rollout):
    [listed] = lines_runs.index()
    assert (listed["env"], listed["models"], listed["failed"]) == (LINES_ENV, [SONNET], [])
    [e], scored = lines_runs.episodes(E2E_RUN), ROW
    assert (e["env"], e["optimal_cost"], e["naive_cost"], e["rolling_cost"], e["silent_cost"], e["hindsight_cost"],
            e["watches"], e["weather"]) == (
        LINES_ENV, REF["optimal_cost"], REF["naive"]["cost"], REF["rolling"]["cost"], REF["silent"]["cost"],
        REF["hindsight_cost"], len(REF["watch_hours"]), LINES_TASK.rsplit("-", 1)[1])
    assert (e["reward"], e["anchor_hours"], e["messages"], e["regret"], e["confirms"]) == (
        scored["reward"], scored["anchor_hours"], scored["messages"], scored["regret"],
        sum(s["tool"] == "confirm_berths" for s in recorded()["steps"]))
    assert rollout["live"]["reference"] == {
        "optimal_cost": REF["optimal_cost"], "unavoidable_cost": REF["unavoidable_cost"],
        "rolling": played(REF["rolling"]), "naive": REF["naive"], "hindsight_cost": REF["hindsight_cost"],
        "silent": played(REF["silent"])}
    assert rollout["live"]["lines"]["firms"] == TASK.rules["lines"]["firms"]


def test_the_explorer_serves_a_lines_week_from_the_lines_pack_unless_a_wind_sweep_has_it(tmp_path):
    shutil.copytree(LINES_ROOT / E2E_RUN, tmp_path / E2E_RUN)
    runs = Runs(tmp_path)

    def get(path: str):
        return json.loads(route(runs, tmp_path, path)[2])

    assert get(f"/api/tasks/{LINES_TASK}") == TASK.to_dict(public=True)
    assert get(f"/api/tasks/{LINES_TASK}/reference") == TASK.reference
    assert [t["task_id"] for t in get("/api/tasks")] == [LINES_TASK]
    shutil.copytree(LINES_ROOT / E2E_RUN, tmp_path / "wind-copy")
    spec = tmp_path / "wind-copy/sweep.json"
    spec.write_text(json.dumps({k: v for k, v in json.loads(spec.read_text()).items() if k != "lines"}
                               | {"wind": True}))
    runs = Runs(tmp_path)
    assert runs.task(LINES_TASK) is runs.wind_pack.get(LINES_TASK)


def test_v1_to_v4_steps_and_rollouts_carry_no_lines_state(runs, monkeypatch):
    use(monkeypatch)
    rollouts = [runs.rollout(*episode) for episode in LIVE] + [
        Runs(MARINE_ROOT).rollout(MARINE_RUN, "scripted/rolling", MARINE_TASK),
        Runs(WIND_ROOT).rollout(WIND_RUN, "scripted/rolling", WIND_TASK)]
    for ro in rollouts:
        assert not any("lines" in s or s["tool"] == MESSAGE_TOOL for s in ro["steps"])
        assert "lines" not in ro["live"] and "silent" not in ro["live"]["reference"]


def test_v1_to_v4_are_viewed_without_a_lines_pack(monkeypatch, tmp_path):
    monkeypatch.setattr(lines, "pack_dir", lambda: tmp_path / "no-pack")
    monkeypatch.setattr(lines, "REFERENCES", tmp_path / "no-references.jsonl")
    for root in (ROOT, MARINE_ROOT):
        runs = Runs(root)
        assert all(not r["failed"] for r in runs.index()) and runs.tasks()
        assert route(runs, root, f"/api/tasks/{LINES_TASK}")[0] == 404
    with pytest.raises(FileNotFoundError):
        Runs(LINES_ROOT).index()


def test_the_overview_lists_v5_first():
    versions = re.findall(r'\{ env: "([\w-]+)", v: "(v\d)", name: "([^"]+)"', (EXT / "overview.js").read_text())
    assert versions == [("portsim-lines", "v5", "the lines port"), ("portsim-wind", "v4", "the wind port"),
                        ("portsim-marine", "v3", "the marine port"), ("portsim-live", "v2", "the live port"),
                        ("portsim", "v1", "a week planned in one go")]


def test_a_film_holds_each_message_for_less_than_a_plan(rollout):
    steps = rollout["steps"]
    frames = record.timeline({"steps": steps, "live": {}}, 250, fps=10, step_seconds=2, message_seconds=0.5)
    held = {k: sum(f.step == k for f in frames) for k in range(1, len(steps) - 1)
            if steps[k]["hour"] == steps[k - 1]["hour"]}
    assert {n for k, n in held.items() if steps[k]["tool"] == MESSAGE_TOOL} == {5}
    assert {n for k, n in held.items() if steps[k]["tool"] == "confirm_berths"} == {20}
    assert sorted({f.step for f in frames}) == list(range(len(steps)))


SCENE = """import("/viewer/ext/stage.js").then(({ currentStage }) => {
  const { chart, scene } = currentStage();
  const held = (id) => {
    const a = scene.actors.get(`s${id}`);
    const s = a && a.sched.segs.find((x) => x.kind === "hold" && x.phase !== "alongside");
    return s ? s.t0 : null;
  };
  const arrivals = (week) => Object.fromEntries(week.ships.map((s) => [s.id, s.arrival]));
  return { chart: arrivals(chart.task), scene: arrivals(scene.task),
           held: Object.fromEntries(chart.task.ships.map((s) => [s.id, held(s.id)])) };
})"""


def plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def first_agreed(steps: list[dict], ship: int) -> int:
    return next(k for k, s in enumerate(steps) if s["tool"] == MESSAGE_TOOL
                and any(a["ship"] == ship for a in s["lines"]["agreed"]))


@pytest.mark.browser
@pytest.mark.parametrize("layout", record.LAYOUTS)
def test_the_panel_shows_the_watchs_exchanges_and_the_agreed_arrivals(lines_runs, rollout, layout):
    steps, firms, ship = rollout["steps"], rollout["live"]["lines"]["firms"], slowed(rollout)
    k = first_agreed(steps, ship)
    e = next(x for x in own(steps, k) if x["ship"] == ship)
    with opened(lines_runs, EPISODE, layout) as (page, horizon):
        page.js(f"portsim.show({k})")
        page.js(f"portsim.time({steps[k]['hour']})")
        shown = page.js(PANEL)
        agreed = steps[k]["lines"]["agreed"]
        due = ", ".join(f"{TASK.ships[a['ship']].name} h{a['arrival']}" for a in agreed
                        if a["arrival"] > steps[k]["hour"])
        n = len(steps[k]["lines"]["exchanges"])
        assert " ".join(shown[0].split()) == (
            f"Ships' agents · {plural(n, 'request')} this watch · {plural(len(agreed), 'arrival')} agreed · due: {due}")
        assert (f"{firms[e['firm']]} {TASK.ships[ship].name}: asked h{e['arrival']} → agreed h{e['arrival']}, slowing"
                in [x.strip() for x in shown[1:]])
        assert page.js("document.querySelectorAll('.ps-exch li.new').length") == len(own(steps, k))
        assert len(shown) == 1 + min(n, 4) + (n > 4)
        page.js(f"portsim.show({len(steps) - 1})")
        page.js(f"portsim.time({horizon})")
        assert page.js("document.querySelectorAll('.ps-exch li.new').length") == 0
        assert page.js(PANEL)[0].endswith(f"{plural(len(steps[-1]['lines']['agreed']), 'arrival')} agreed")
        assert page.js("document.querySelector('.ps-final').innerText").count("Hours at anchor") == 1


@pytest.mark.browser
def test_a_slowed_ship_waits_at_sea_until_its_agreed_hour(lines_runs, rollout):
    steps = rollout["steps"]
    final = {a["ship"]: a["arrival"] for a in steps[-1]["lines"]["agreed"]}
    late = [s for s, h in final.items() if h > TASK.ships[s].arrival]
    ship = slowed(rollout)
    with opened(lines_runs, EPISODE, "full") as (page, horizon):
        k = first_agreed(steps, ship)
        page.js(f"portsim.show({k})")
        seen = page.js(SCENE)
        assert seen["chart"] == seen["scene"] == {str(s["id"]): s["arrival"] for s in steps[k]["task"]["ships"]}
        then = next(a["arrival"] for a in steps[k]["lines"]["agreed"] if a["ship"] == ship)
        assert seen["scene"][str(ship)] == then > TASK.ships[ship].arrival
        page.js(f"portsim.show({len(steps) - 1})")
        page.js(f"portsim.time({horizon})")
        seen = page.js(SCENE)
        assert seen["scene"] == {str(s.id): final.get(s.id, s.arrival) for s in TASK.ships}
        for s in late:
            held = seen["held"][str(s)]
            assert TASK.ships[s].arrival - 2 < held and final[s] - 3 < held <= final[s] - 2


@pytest.mark.browser
def test_the_overview_heads_with_the_v5_board(monkeypatch, tmp_path):
    use(monkeypatch)
    for root, run in ((LINES_ROOT, E2E_RUN), (WIND_ROOT, WIND_RUN), (MARINE_ROOT, MARINE_RUN), (ROOT, LIVE[0][0])):
        shutil.copytree(root / run, tmp_path / run)
    with opened(Runs(tmp_path), EPISODE, "full") as (page, _):
        page.js("location.hash = '#/'")
        page.js("new Promise((r) => { const f = () => document.querySelector('#ps-runs .ps-run') ? r() : "
                "setTimeout(f, 100); f(); })")
        heads = page.js("[...document.querySelectorAll('#ps-runs .ps-run h2')].map((h) => h.textContent)")
        assert heads == ["v5 · the lines port", "v4 · the wind port", "v3 · the marine port", "v2 · the live port"]
        board = page.js("document.querySelector('#ps-runs .ps-run th:last-child').textContent")
        cols = page.js("[...document.querySelectorAll('#ov-eps thead th')].map((h) => h.textContent)")
        assert board == "At the anchor"
        assert {"Anchor", "Follower", "Silent", "Hindsight", "At anchor", "Requests"} <= set(cols)
