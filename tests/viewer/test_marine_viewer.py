"""The viewer on a marine run: replayed through a MarineWeek against the marine pack and references, each step with the
pilots and tugs the marine checker counts, the explorer's week by mode, and (with Chrome and the network) the panel's
pilots and tugs line in both layouts."""

import json
import re
import shutil
import threading
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager

import berth_core
import pytest
from berth_core import plan_from_list
from recorded import LIVE, MARINE_ROOT, MARINE_RUN, MARINE_TASK, POLICIES, marine_run

from agentenv_portsim import marine, record, twin
from agentenv_portsim.episodes import Runs
from agentenv_portsim.schedule import MARINE_ENV, SPEAKERS
from agentenv_portsim.sweep import results
from agentenv_portsim.view import route, serve
from agentenv_portsim.world import known, rule

TASK = marine.pack().get(MARINE_TASK)
REF = next(r for r in marine.references() if r["task_id"] == MARINE_TASK)
ROWS = {r["model"]: r for r in results(MARINE_ROOT / MARINE_RUN)}
GRADE = ("cost", "reward", "feasible", "excused_cost")
NAIVE, ROLLING = POLICIES
PANEL = '[...document.querySelectorAll(".ps-marine")].map((e) => e.innerText)'


@pytest.fixture(scope="module")
def marine_runs() -> Runs:
    return Runs(MARINE_ROOT)


def recorded(model: str) -> dict:
    return json.loads((MARINE_ROOT / MARINE_RUN / ROWS[model]["transcript"]).read_text())


def test_the_synthetic_run_is_rebuilt_byte_for_byte(tmp_path):
    marine_run(tmp_path)
    ours = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file())
    assert ours == sorted(p.relative_to(MARINE_ROOT) for p in MARINE_ROOT.rglob("*") if p.is_file())
    assert all((tmp_path / p).read_bytes() == (MARINE_ROOT / p).read_bytes() for p in ours)


@pytest.mark.parametrize("model", POLICIES)
def test_a_marine_replay_gives_back_every_recorded_step_and_the_stored_grade(marine_runs, model):
    ro, row, rec = marine_runs.rollout(MARINE_RUN, model, MARINE_TASK), ROWS[model], recorded(model)
    assert [(s["turn"], s["tool"], s["entries"]) for s in ro["steps"]] == [
        (s["turn"], s["tool"], s["plan"]) for s in rec["steps"]]
    assert [{k: v for k, v in s["result"].items() if k != "violations"} for s in ro["steps"]] == [
        s["result"] for s in rec["steps"]]
    grade, stored = ro["final"]["grade"], REF[POLICIES[model][0]]
    assert ro["reward"] == row["reward"] == rec["reward"] == stored["reward"]
    assert {k: grade[k] for k in GRADE} == {k: stored[k] for k in GRADE}
    assert (grade["optimal_cost"], grade["regret"]) == (REF["optimal_cost"], row["regret"])
    assert ro["live"]["audit"] == {"ok": True, "problems": []}
    assert [w["hour"] for w in ro["live"]["watches"]] == REF["watch_hours"]
    assert ro["live"]["reference"]["naive"] == REF["naive"]


def test_the_naive_week_breaks_only_the_pilot_and_tug_rule(marine_runs):
    grade = marine_runs.rollout(MARINE_RUN, NAIVE, MARINE_TASK)["final"]["grade"]
    assert {rule(v["problem"]) for v in grade["violations"]} == {"pilots", "tugs"}
    assert {"ship": 2, "problem": "tugs short at hour 54: your ships need 4, 2 free"} in grade["violations"]


@pytest.mark.parametrize("model", POLICIES)
def test_each_step_holds_the_free_pilots_and_tugs_and_the_plans_use_as_the_marine_checker_counts_them(
        marine_runs, model):
    for step in marine_runs.rollout(MARINE_RUN, model, MARINE_TASK)["steps"]:
        view, plan, m = known(TASK, step["revealed"]), plan_from_list(step["plan"]), step["marine"]
        free = marine.free(view)
        assert (m["hours"], m["pilots"], m["tugs"]) == (264, {"pool": 7, "free": free["pilots"]},
                                                        {"pool": 8, "free": free["tugs"]})
        use = defaultdict(lambda: [0, 0])
        for r in berth_core.evaluate(view, plan).ships:
            if r.berth_hour is not None:
                for hour in (r.berth_hour, r.departure):
                    windy = any(a <= hour < b for a, b in marine.wind(view))
                    use[hour][0] += 1
                    use[hour][1] += marine.tugs_needed(marine.CONTAINER, view.ships[r.ship].length_m, windy)
        assert m["ours"] == [[hour, *n] for hour, n in sorted(use.items())]
        short = {h for h, pilots, tugs in m["ours"] if pilots > free["pilots"][h] or tugs > free["tugs"][h]}
        assert short == {int(re.search(r"at hour (\d+)", p)[1]) for r in marine.evaluate(view, plan).ships
                         for p in r.problems if rule(p) in ("pilots", "tugs")}
        assert m["cuts"] == [{"from": SPEAKERS[e["type"]], "pool": marine.CUTS[e["type"]],
                              "count": e[marine.CUTS[e["type"]]], "start": e["start"], "end": e["end"]}
                             for e in view.disruptions if e["type"] in marine.CUTS]


def test_the_cuts_arrive_with_the_tuesday_bulletin(marine_runs):
    ro = marine_runs.rollout(MARINE_RUN, ROLLING, MARINE_TASK)
    news = [(b["from"], b["hour"], b["text"]) for b in ro["live"]["bulletins"] if b["kind"] in marine.CUTS]
    assert news == [("Tug company", 30, "2 of the port's 8 tugs are out of service from hour 54 to hour 78: 6 tugs in "
                                        "that window."),
                    ("Pilot station", 30, "2 of the port's 7 pilots on duty are unavailable from hour 54 to hour 66: "
                                          "5 pilots in that window.")]
    assert [len(s["marine"]["cuts"]) for s in ro["steps"]] == [0 if s["hour"] < 30 else 2 for s in ro["steps"]]


def test_a_marine_run_is_listed_on_portsim_marine_with_the_marine_references(marine_runs):
    [listed] = marine_runs.index()
    assert (listed["env"], listed["models"], listed["mean_reward"]) == (
        MARINE_ENV, sorted(POLICIES), round((REF["naive"]["reward"] + REF["rolling"]["reward"]) / 2, 4))
    for e in marine_runs.episodes(MARINE_RUN):
        assert (e["env"], e["optimal_cost"], e["naive_cost"], e["rolling_cost"], e["watches"]) == (
            MARINE_ENV, TASK.reference["optimal_cost"], REF["naive"]["cost"], REF["rolling"]["cost"], 7)


def test_v2_steps_carry_no_marine_state(runs):
    for run, model, task_id in LIVE:
        assert not any("marine" in s for s in runs.rollout(run, model, task_id)["steps"])


def test_the_explorer_shows_the_marine_week_only_when_every_run_of_it_is_marine(tmp_path):
    shutil.copytree(MARINE_ROOT / MARINE_RUN, tmp_path / MARINE_RUN)
    runs = Runs(tmp_path)

    def get(path: str):
        return json.loads(route(runs, tmp_path, path)[2])

    assert get(f"/api/tasks/{MARINE_TASK}") == TASK.to_dict(public=True)
    assert get(f"/api/tasks/{MARINE_TASK}/reference") == TASK.reference
    assert get("/api/tasks")[0]["disruptions"][-2:] == ["tug_outage", "pilot_shortage"]
    shutil.copytree(MARINE_ROOT / MARINE_RUN, tmp_path / "live-copy")
    spec = tmp_path / "live-copy/sweep.json"
    spec.write_text(json.dumps({k: v for k, v in json.loads(spec.read_text()).items() if k != "marine"}))
    runs = Runs(tmp_path)
    assert runs.task(MARINE_TASK) is runs.pack.get(MARINE_TASK)
    assert get(f"/api/tasks/{MARINE_TASK}") == runs.pack.public(runs.pack.get(MARINE_TASK)) != TASK.to_dict(public=True)


def panel_line(step: dict, hour: int) -> str:
    m = step["marine"]
    _, pilots, tugs = next((o for o in m["ours"] if o[0] == hour), (hour, 0, 0))
    free = {pool: m[pool]["free"][hour] if hour < m["hours"] else m[pool]["pool"] for pool in ("pilots", "tugs")}
    short = " · short" if pilots > free["pilots"] or tugs > free["tugs"] else ""
    cuts = "".join(f" · {c['from']}: {c['count']} out h{c['start']}–{c['end']}" for c in m["cuts"]
                   if c["start"] <= hour < c["end"])
    return (f"h{hour} · pilots: ours {pilots}, free {free['pilots']} · tugs: ours {tugs}, free {free['tugs']}"
            f"{short}{cuts}")


@contextmanager
def opened(runs: Runs, episode: tuple[str, str, str], layout: str) -> Iterator[tuple[record.Page, float]]:
    server = serve(runs, twin.ensure(), 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = record.episode_url(server.server_port, *episode, layout)
        with record.recording(url, record.find_chrome(None), 1920, 1080) as (page, ready):
            yield page, ready["horizon"]
    finally:
        server.shutdown()
        server.server_close()


def lines(page: record.Page, k: int, hour: float) -> list[str]:
    page.js(f"portsim.show({k})")
    page.js(f"portsim.time({hour})")
    return page.js(PANEL)


@pytest.mark.browser
@pytest.mark.parametrize("layout", record.LAYOUTS)
def test_the_panel_shows_the_hours_pilots_and_tugs_in_both_layouts(marine_runs, runs, layout):
    steps = marine_runs.rollout(MARINE_RUN, NAIVE, MARINE_TASK)["steps"]
    last = len(steps) - 1
    with opened(marine_runs, (MARINE_RUN, NAIVE, MARINE_TASK), layout) as (page, horizon):
        assert lines(page, last, 54.5) == ["h54 · pilots: ours 2, free 2 · tugs: ours 4, free 2 · short · Tug company: "
                                           "2 out h54–78 · Pilot station: 2 out h54–66"]
        assert lines(page, 2, 30) == [panel_line(steps[2], 30)]
        assert lines(page, last, horizon) == [panel_line(steps[last], int(horizon))]
        card = page.js("document.querySelector('.ps-watch').getBoundingClientRect().top")
        head = page.js("document.querySelector('.page-head').getBoundingClientRect().bottom")
        assert layout == "full" or card > head
    with opened(runs, LIVE[0], layout) as (page, horizon):
        assert lines(page, 0, 0) == lines(page, len(runs.rollout(*LIVE[0])["steps"]) - 1, horizon) == []
