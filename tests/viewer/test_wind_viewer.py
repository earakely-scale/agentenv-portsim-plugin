"""The viewer on a wind run (the synthetic one, on the wind fixtures): replayed through a WindWeek against the wind pack
and references, each step with the forecast in force as wind.step_wind gives it, the bust week's hold re-plan, the
explorer's week, v1 to v3 viewed without a wind pack, and (with Chrome and the network) the panel's wind line and strip
in both layouts, with the 3D quay in the wind that blew."""

import json
import shutil

import berth_core
import pytest
from berth_core import MOVE_PENALTY, TaskPack, plan_from_list
from recorded import (
    LIVE,
    MARINE_ROOT,
    MARINE_RUN,
    MARINE_TASK,
    ROOT,
    WIND_FIXTURES,
    WIND_POLICIES,
    WIND_ROOT,
    WIND_RUN,
    WIND_TASK,
    wind_run,
)
from test_marine_viewer import opened
from wind_fixtures import BUST_TASK, FIXTURES, PACK_DIR, REFERENCES, STORM_TASK, use

from agentenv_portsim import record, wind
from agentenv_portsim.episodes import Runs, env
from agentenv_portsim.schedule import SPEAKERS, WIND_ENV
from agentenv_portsim.sweep import Sweep, results
from agentenv_portsim.view import route

PACK = TaskPack(PACK_DIR)
TASK = PACK.get(WIND_TASK)
REFS = {r["task_id"]: r for r in map(json.loads, REFERENCES.read_text().splitlines())}
REF = REFS[WIND_TASK]
ROWS = {r["model"]: r for r in results(WIND_ROOT / WIND_RUN)}
GRADE = ("cost", "reward", "feasible", "excused_cost")
BLIND, ROLLING = WIND_POLICIES
PANEL = '[...document.querySelectorAll(".ps-wind")].map((e) => e.innerText)'
CREDIT = "Forecast: ECMWF open data, CC BY 4.0, modified · Observed: Meteocat XEMA Y7, derived windows"


@pytest.fixture(scope="module", autouse=True)
def fixtures():
    with pytest.MonkeyPatch.context() as mp:
        use(mp)
        yield


@pytest.fixture(scope="module")
def wind_runs(fixtures) -> Runs:
    return Runs(WIND_ROOT)


def recorded(model: str) -> dict:
    return json.loads((WIND_ROOT / WIND_RUN / ROWS[model]["transcript"]).read_text())


def played(policy: dict) -> dict:
    return {k: v for k, v in policy.items() if k not in ("plans", "configs")}


def test_the_synthetic_run_is_rebuilt_byte_for_byte_from_the_wind_fixtures(tmp_path):
    assert (WIND_FIXTURES, WIND_TASK) == (FIXTURES, STORM_TASK) and wind.task_ids()[0] == WIND_TASK
    wind_run(tmp_path)
    ours = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file())
    assert ours == sorted(p.relative_to(WIND_ROOT) for p in WIND_ROOT.rglob("*") if p.is_file())
    assert all((tmp_path / p).read_bytes() == (WIND_ROOT / p).read_bytes() for p in ours)


def test_the_run_is_a_wind_sweep_as_sweep_json_records_one():
    spec = json.loads((WIND_ROOT / WIND_RUN / "sweep.json").read_text())
    assert "marine" not in spec and Sweep(**spec) == Sweep(WIND_RUN, list(WIND_POLICIES), [WIND_TASK], 1, 5.0,
                                                          live=True, wind=True)
    assert env(Sweep(**spec)) == WIND_ENV


@pytest.mark.parametrize("model", WIND_POLICIES)
def test_a_wind_replay_gives_back_every_recorded_step_and_the_stored_grade(wind_runs, model):
    ro, row, rec = wind_runs.rollout(WIND_RUN, model, WIND_TASK), ROWS[model], recorded(model)
    assert [(s["turn"], s["tool"], s["entries"]) for s in ro["steps"]] == [
        (s["turn"], s["tool"], s["plan"]) for s in rec["steps"]]
    assert [{k: v for k, v in s["result"].items() if k != "violations"} for s in ro["steps"]] == [
        s["result"] for s in rec["steps"]]
    grade, stored = ro["final"]["grade"], REF[WIND_POLICIES[model][0]]
    assert ro["reward"] == row["reward"] == rec["reward"] == stored["reward"]
    assert {k: grade[k] for k in GRADE} == {k: stored[k] for k in GRADE}
    assert (grade["optimal_cost"], grade["regret"]) == (REF["optimal_cost"], row["regret"])
    assert ro["live"]["audit"] == {"ok": True, "problems": []}
    assert [w["hour"] for w in ro["live"]["watches"]] == REF["watch_hours"]
    assert ro["live"]["reference"] == {"optimal_cost": REF["optimal_cost"], "unavoidable_cost": REF["unavoidable_cost"],
                                       "rolling": played(REF["rolling"]), "naive": REF["naive"],
                                       "hindsight_cost": REF["hindsight_cost"], "blind": played(REF["blind"])}


def test_the_follower_scores_the_anchor_net_of_its_waivers_and_the_blind_one_breaks_a_rule(wind_runs):
    ro = wind_runs.rollout(WIND_RUN, ROLLING, WIND_TASK)
    rolling, blind = ro["final"]["grade"], wind_runs.rollout(WIND_RUN, BLIND, WIND_TASK)["final"]["grade"]
    assert rolling["excused"] and rolling["cost"] == REF["optimal_cost"] < REF["hindsight_cost"]
    moved = sum(r.moved for r in berth_core.evaluate(TASK, plan_from_list(ro["final"]["plan"])).ships)
    assert (rolling["moves"], rolling["delay_cost"]) == (moved, rolling["cost"] - MOVE_PENALTY * moved)
    assert not blind["feasible"] and blind["reward"] < 0.9


@pytest.mark.parametrize("model", WIND_POLICIES)
def test_each_step_holds_the_forecast_in_force_as_step_wind_gives_it(wind_runs, model):
    for step in wind_runs.rollout(WIND_RUN, model, WIND_TASK)["steps"]:
        view = wind.known(TASK, step["revealed"])
        assert step["wind"] == wind.step_wind(view) and step["task"] == view.to_dict(public=True)
        hours = [TASK.disruptions[int(i.rsplit("-", 1)[1])]["hour"] for i in step["revealed"]
                 if i.startswith("forecast-")]
        assert step["wind"]["hour"] == max(hours) == step["hour"]
        assert all(h >= step["hour"] for h, _ in step["wind"]["kn"])
        assert [{k: w[k] for k in ("start", "end", "min_length")} for w in step["task"]["rules"]["no_moves"]] == (
            step["wind"]["observed"] + step["wind"]["windows"])


def test_port_control_sends_the_forecast_at_every_watch_last_among_its_notices(wind_runs):
    ro = wind_runs.rollout(WIND_RUN, ROLLING, WIND_TASK)
    news = ro["live"]["bulletins"]
    forecasts = [b for b in news if b["kind"] == "forecast"]
    assert [b["hour"] for b in forecasts] == REF["watch_hours"]
    assert all(b["from"] == SPEAKERS["forecast"] for b in forecasts)
    entries = [e for e in TASK.disruptions if e["type"] == "forecast"]
    assert [b["text"] for b in forecasts] == [wind.notice(e) for e in entries]
    for b in forecasts:
        assert [x for x in news if x["watch"] == b["watch"]][-1] is b
    assert forecasts[0]["via"] == "load" and {b["via"] for b in forecasts[1:]} == {"trigger"}


def test_a_wind_run_is_listed_on_portsim_wind_with_the_wind_references(wind_runs):
    [listed] = wind_runs.index()
    assert (listed["env"], listed["models"], listed["mean_reward"]) == (
        WIND_ENV, sorted(WIND_POLICIES), round((REF["blind"]["reward"] + REF["rolling"]["reward"]) / 2, 4))
    for e in wind_runs.episodes(WIND_RUN):
        assert (e["env"], e["optimal_cost"], e["naive_cost"], e["rolling_cost"], e["watches"], e["weather"],
                e["hindsight_cost"]) == (WIND_ENV, TASK.reference["optimal_cost"], REF["naive"]["cost"],
                                         REF["rolling"]["cost"], len(REF["watch_hours"]), REF["weather"],
                                         REF["hindsight_cost"])


def test_a_bust_weeks_reference_carries_the_hold_re_plan(tmp_path):
    wind_run(tmp_path, (BUST_TASK,))
    runs, ref = Runs(tmp_path), REFS[BUST_TASK]
    for model in WIND_POLICIES:
        ro = runs.rollout(WIND_RUN, model, BUST_TASK)
        assert ro["reward"] == ref[WIND_POLICIES[model][0]]["reward"]
        assert {k: ro["live"]["reference"][k] for k in ("blind", "hold")} == {
            "blind": played(ref["blind"]), "hold": played(ref["hold"])}


def test_v2_and_v3_steps_and_references_carry_no_wind_state(runs):
    marine_ro = Runs(MARINE_ROOT).rollout(MARINE_RUN, "scripted/rolling", MARINE_TASK)
    for ro in [marine_ro] + [runs.rollout(*episode) for episode in LIVE]:
        assert not any("wind" in s for s in ro["steps"])
        assert list(ro["live"]["reference"]) == ["optimal_cost", "unavoidable_cost", "rolling", "naive"]


def test_the_explorer_serves_a_wind_week_from_the_wind_pack(tmp_path):
    shutil.copytree(WIND_ROOT / WIND_RUN, tmp_path / WIND_RUN)
    shutil.copytree(MARINE_ROOT / MARINE_RUN, tmp_path / MARINE_RUN)
    runs = Runs(tmp_path)

    def get(path: str):
        return json.loads(route(runs, tmp_path, path)[2])

    assert get(f"/api/tasks/{WIND_TASK}") == TASK.to_dict(public=True)
    assert get(f"/api/tasks/{WIND_TASK}/reference") == TASK.reference
    listed = {t["task_id"]: t for t in get("/api/tasks")}
    assert listed[WIND_TASK]["disruptions"][-len(REF["watch_hours"]):] == ["forecast"] * len(REF["watch_hours"])
    assert get(f"/api/tasks/{MARINE_TASK}")["task_id"] == MARINE_TASK
    assert route(runs, tmp_path, f"/api/tasks/{BUST_TASK}")[0] == 404


def test_v1_to_v3_are_viewed_without_a_wind_pack(monkeypatch, tmp_path):
    monkeypatch.setattr(wind, "pack_dir", lambda: tmp_path / "no-pack")
    monkeypatch.setattr(wind, "REFERENCES", tmp_path / "no-references.jsonl")
    for root in (ROOT, MARINE_ROOT):
        runs = Runs(root)
        assert all(not r["failed"] for r in runs.index()) and runs.tasks()
        assert route(runs, root, f"/api/tasks/{WIND_TASK}")[0] == 404
    with pytest.raises(FileNotFoundError):
        Runs(WIND_ROOT).index()


def wind_line(w: dict) -> str:
    def spans(ws: list[dict]) -> str:
        return ", ".join(f"{x['start']}–{x['end']}" for x in ws if x["min_length"] > 0) or "none"

    return (f"Wind h{w['hour']} · Port Control, issued {w['time']}: >25 kn {spans(w['windows'])} · "
            f"observed {spans(w['observed'])}")


STRIP = """(() => { const s = document.querySelector(".ps-wind-strip"); const box = s.getBoundingClientRect();
  const rects = (cls) => [...s.querySelectorAll(`.${cls}`)].map((r) => ["x", "width"].map((k) => +r.getAttribute(k)));
  const banner = document.querySelector(".scene-wind");
  return {size: [box.width, box.height], w25: rects("ps-ws-w25"), w30: rects("ps-ws-w30"), o25: rects("ps-ws-o25"),
          o30: rects("ps-ws-o30"), cursor: +s.querySelector(".ps-ws-cursor").getAttribute("x1"),
          credit: s.querySelector(".ps-ws-credit").textContent, banner: banner.hidden ? null : banner.textContent};
})()"""


def at(page: record.Page, k: int, hour: float) -> dict:
    page.js(f"portsim.show({k})")
    page.js(f"portsim.time({hour})")
    return {"lines": page.js(PANEL), **page.js(STRIP)}


@pytest.mark.browser
@pytest.mark.parametrize("layout", record.LAYOUTS)
def test_the_panel_shows_the_forecast_and_the_strip_and_the_3d_quay_the_wind_that_blew(wind_runs, runs, layout):
    steps = wind_runs.rollout(WIND_RUN, ROLLING, WIND_TASK)["steps"]
    first = {h: next(k for k, s in enumerate(steps) if s["hour"] == h) for h in REF["watch_hours"]}
    blew = [w for w in TASK.rules["no_moves"] if w["min_length"] == 300]
    with opened(wind_runs, (WIND_RUN, ROLLING, WIND_TASK), layout) as (page, horizon):
        def span(a: float, b: float) -> list:
            return pytest.approx([a / horizon * 440, (b - a) / horizon * 440], abs=0.11)

        k = first[30] + 1
        shown = at(page, k, 30)
        assert shown["lines"] == [wind_line(steps[k]["wind"])] and shown["size"] == [440, 48]
        assert shown["w25"] == [span(75, 85)] and shown["o25"] == shown["o30"] == []
        assert (shown["cursor"], shown["credit"], shown["banner"]) == (pytest.approx(30 / horizon * 440, abs=0.06),
                                                                       CREDIT, None)
        assert not any(w["start"] <= 39 < w["end"] for w in steps[first[42] - 1]["task"]["rules"]["no_moves"])
        flying = at(page, first[42], 39)
        assert flying["lines"] == [wind_line(steps[first[42] - 1]["wind"])]
        assert flying["o25"] == [span(blew[0]["start"], 39)]
        assert flying["banner"] == "Wind above 25 kn · ships of 300 m or more may not dock or leave · until Tue 17:00"
        core = at(page, first[72] + 1, 81)
        assert core["banner"].startswith("Wind above 30 kn · no ship may dock or leave") and len(core["o30"]) == 1
        last = at(page, len(steps) - 1, horizon)
        assert last["lines"] == [wind_line(steps[-1]["wind"])] and len(last["o25"]) == len(blew)
        card = page.js("document.querySelector('.ps-watch').getBoundingClientRect().top")
        head = page.js("document.querySelector('.page-head').getBoundingClientRect().bottom")
        assert layout == "full" or card > head
    for other, episode in ((runs, LIVE[0]), (Runs(MARINE_ROOT), (MARINE_RUN, "scripted/rolling", MARINE_TASK))):
        with opened(other, episode, layout) as (page, horizon):
            n = len(other.rollout(*episode)["steps"])
            page.js(f"portsim.show({n - 1})")
            page.js(f"portsim.time({horizon})")
            assert page.js(PANEL) == [] and page.js("document.querySelectorAll('.ps-wind-strip').length") == 0
