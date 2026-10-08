"""The wind tasks, on the synthetic wind pack: a wind week's steps against its marine week's (portsim-wind, a trigger
per watch with the added ones, the forecast last in every bulletin, the gale gone, the opening ending with the wind, the
wind rules), the portsim-wind bundle, `tasks generate --wind`, and `setup` registering portsim-wind on the gateway."""

import json
from importlib.resources import files
from pathlib import Path

import pytest
from agent_env.artifact import DockerImageArtifact
from agent_env.bundle.installed import checked, find_bundle
from agent_env.bundle.parse import BundleKind, parse_bundle
from agent_env.bundle.plan import check_bundle
from agent_env.bundle.resolve import resolve_bundle
from agent_env.env import Env
from agent_env.task_step.registry import get_task_step_registry
from berth_core import TaskPack, rules, situation
from click.testing import CliRunner
from wind_fixtures import BUST_TASK, OTHER_TASK, PACK_DIR, REFERENCES, STORM_TASK, use

from agentenv_portsim import cli, marine, tasks, wind
from agentenv_portsim.cli import portsim
from agentenv_portsim.marine import MarineWeek
from agentenv_portsim.schedule import schedule
from agentenv_portsim.wind import WindWeek

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = files("agentenv_portsim.bundles") / "portsim-wind"
LIVE_BUNDLE = files("agentenv_portsim.bundles") / "portsim-live"
PACK = TaskPack(PACK_DIR)
REFS = {r["task_id"]: r for r in map(json.loads, REFERENCES.read_text().splitlines())}
OPENING = "\n\nIt is watch 0, Monday 00:00. Confirm berth windows with confirm_berths, then call advance."
WIND_RULES = "\n".join([
    "How the week runs:",
    "- The week is played in watches, starting at watch 0 on Monday 00:00 (hour 0). The table shows the week as the "
    "port knows it now. News reaches you as messages in tool results: ships report delays and unscheduled calls, the "
    "harbour master issues emergencies, terminal ops announce closures and crane outages, the line desk flags priority "
    "cargo, and Barcelona Port Control sends the wind forecast at every watch.",
    "- Time only passes when you call advance: the port moves to the next bulletin, ships berth and sail on their "
    "confirmed windows, and the bulletin's messages arrive with your next tool result. Call advance and get_situation "
    "together in one turn.",
    "- From watch 1 on, a window that starts before the freeze line (6 hours after the current hour) is frozen: it "
    "can't be changed, and new or changed windows must start at or after the freeze line. At watch 0 every window is "
    "open.",
    "- You have 3 planning calls (check_plan or confirm_berths) per watch.",
    "",
    "Tools:",
    "- get_situation(): the hour, the week as known now, your confirmed windows (departed, berthed, frozen or open), "
    "the ships still without a window, and new messages.",
    "- check_plan(plan): your entries over your confirmed windows, checked on the week as known now: the ships with a "
    "problem or a cost, the plan's cost, and the entries confirm_berths would refuse. Problems and cost that news "
    "brought to a frozen window are listed as excused and not counted. It confirms nothing.",
    "- confirm_berths(plan): confirms windows with the ships; ships you leave out keep their windows.",
    "- advance(): ends the watch. After the last watch it returns \"done\": the rest of the week runs on your "
    "confirmed windows.",
    "",
    "The week is graded once, on the windows you confirmed and the week as it really happened, in the wind that really "
    "blew: an infeasible week scores low, a feasible one higher the closer its cost is to the best possible. Cost or "
    "rule breaks that news, or wind the forecast didn't show, brings to a window after your last chance to change it "
    "are not charged to you; wind the forecast showed then is. Every ship needs a confirmed window before the week "
    "ends; if you stop before the last watch, the rest of the week runs on the windows you confirmed.",
])
WATCHES = [(1, ["extra-0", "tug_outage-7", "pilot_shortage-8", "forecast-10"]), (2, ["emergency-6", "forecast-11"]),
           (3, ["late-2", "forecast-12"]), (4, ["forecast-13"]), (5, ["late-3", "crane_outage-5", "forecast-14"]),
           (6, ["forecast-15"]), (7, ["bunching-4", "forecast-16"])]


@pytest.fixture(autouse=True)
def fixtures(monkeypatch):
    use(monkeypatch)


def wind_steps(task_id: str, episode_cap_usd: float = 5.0) -> list[dict]:
    return tasks.live_steps(PACK.get(task_id), episode_cap_usd, env="portsim-wind", week=WindWeek,
                            rules=tasks.WIND_RULES)


def marine_steps(task_id: str) -> list[dict]:
    return tasks.live_steps(marine.pack().get(task_id), 5.0, env="portsim-marine", week=MarineWeek)


def actions(steps: list[dict]) -> list[list[dict]]:
    return [t["actions"] for t in next(s for s in steps if s["id"] == "watches")["triggers"]]


def bundled(name: str) -> list[dict]:
    return json.loads(BUNDLE.joinpath(f"tasks/{name}.json").read_text())


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_a_wind_week_is_its_marine_week_on_portsim_wind_with_the_forecast_last_in_every_bulletin():
    task, steps = PACK.get(STORM_TASK), wind_steps(STORM_TASK)
    v3 = marine_steps("dock-24B-w07x1-busy-0")
    assert [s["id"] for s in steps] == [s["id"] for s in v3]
    assert {s.get("env_id") for s in steps} == {"portsim-wind", None}
    assert steps[1]["directives"] == [{"service": "portsim-wind", "uri": "urn:portsim:live-load/v1",
                                       "args": {"task_id": STORM_TASK}}]
    assert steps[7]["directives"][0]["service"] == "portsim-wind" and steps[4]["env_ids"] == ["portsim-wind"]
    assert steps[5] == {**v3[5], "env_id": "portsim-wind"}
    watches = steps[3]["triggers"]
    assert [(t["id"], [a["args"]["event_id"] for a in t["actions"]]) for t in watches] == [
        (f"watch-{k}", events) for k, events in WATCHES]
    assert [w.hour for w in schedule(task)] == REFS[STORM_TASK]["watch_hours"] == [0, 30, 42, 54, 72, 84, 90, 120]
    assert REFS[STORM_TASK]["added_watches"] == [72]
    forecasts = [e for e in task.disruptions if e["type"] == "forecast"]
    assert [bulletin[-1]["args"] for bulletin in actions(steps)] == [
        {"event_id": f"forecast-{task.disruptions.index(e)}", "name": "Barcelona Port Control", "text": wind.notice(e)}
        for e in forecasts[1:]]
    assert actions(steps)[0][-1]["args"]["text"] == (
        "Wind forecast issued Tue 03:00 (ECMWF, adjusted to the Dique Sur anemometer), to hour 90: above 25 kn hours "
        "75–85, peak 32 kn; above 30 kn 77–80.")
    news = [(a["args"]["name"], a["args"]["text"]) for bulletin in actions(steps) for a in bulletin[:-1]]
    assert news == [(a["args"]["name"], a["args"]["text"]) for bulletin in actions(v3) for a in bulletin
                    if not a["args"]["event_id"].startswith("gale-")]
    assert all(a["args"]["text"] == task.notices[int(a["args"]["event_id"].rsplit("-", 1)[1])]
               for bulletin in actions(steps) for a in bulletin)


def test_a_bust_week_keeps_the_gales_watch_for_its_forecast():
    steps = wind_steps(BUST_TASK)
    assert [[a["args"]["event_id"] for a in bulletin] for bulletin in actions(steps)] == [
        ["extra-0", "tug_outage-7", "pilot_shortage-8", "forecast-10"], ["emergency-6", "forecast-11"],
        ["late-2", "forecast-12"], ["late-3", "crane_outage-5", "forecast-13"], ["forecast-14"],
        ["bunching-4", "forecast-15"]]
    assert REFS[BUST_TASK]["added_watches"] == []


def test_the_wind_opening_ends_with_the_wind_and_the_rules_are_the_wind_rules():
    task = PACK.get(STORM_TASK)
    play = next(s for s in wind_steps(STORM_TASK) if s["id"] == "play")
    view = wind.known(task, ["closure-1", "forecast-9"])
    assert play["prompt"] == (situation(view) + "\n\n" + marine.section(view) + "\n\n" + wind.section(view) + OPENING)
    assert play["prompt"].endswith("\n- Observed since hour 0: no hour above 25 kn." + OPENING)
    assert "MAERSK NUBA" not in play["prompt"] and "Tug company" not in play["prompt"]
    assert play["system_prompt"] == rules(task, 3).split("\n\nTools:\n")[0] + "\n\n" + WIND_RULES
    assert tasks.WIND_RULES == WIND_RULES and tasks.live_rules(task, tasks.WIND_RULES) == play["system_prompt"]
    assert play["max_turns"] == 47


def test_the_wind_rules_are_the_live_rules_with_two_sentences_changed():
    live, ours = tasks.LIVE_RULES.split("\n"), WIND_RULES.split("\n")
    assert [i for i, (a, b) in enumerate(zip(live, ours, strict=True)) if a != b] == [1, len(live) - 1]
    assert ours[-1].endswith(live[-1].rpartition("are not charged to you. ")[2])


def test_the_wind_bundle_installs_week_and_wiring_noplay_and_the_live_verifier(local_stores):
    bundle = checked(find_bundle("portsim-wind"))
    entries = {(e.kind, e.name): e for e in bundle.entries}
    assert bundle.description.startswith(
        "PortSim wind: one week at a Port of Barcelona quay played in watches on the gateway's virtual clock, with the "
        "port's pilots and tugs, in a real weather week at the Dique Sur anemometer")
    assert sorted(name for kind, name in entries if kind is BundleKind.TASK) == ["week", "wiring-noplay"]
    assert entries[BundleKind.ARTIFACT, "portsim-live-verifier"].type == "file"
    assert BUNDLE.joinpath("artifacts/portsim-live-verifier/verify.py").read_bytes() == LIVE_BUNDLE.joinpath(
        "artifacts/portsim-live-verifier/verify.py").read_bytes()
    assert wind.task_ids()[0] == STORM_TASK
    week = wind_steps(STORM_TASK)
    assert bundled("week") == week
    assert bundled("wiring-noplay") == [s for s in week if s["id"] not in ("deploy-agent", "play")]
    registry = get_task_step_registry()
    for name in ("week", "wiring-noplay"):
        text = BUNDLE.joinpath(f"tasks/{name}.json").read_text()
        assert text == json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n"
        assert {registry[s["type"]].from_dict(s).env_id for s in bundled(name) if "env_id" in s} == {"portsim-wind"}
    names = ("portsim", "portsim-live", "portsim-marine", "portsim-wind")
    assert len({find_bundle(name).root for name in names}) == 4


def test_generate_wind_writes_the_qualifying_wind_weeks_the_live_verifier_and_the_readme(tmp_path, local_stores):
    out = tmp_path / "wind"
    names = tasks.generate("dock-v1-eval", out, wind=True)
    assert names == [t.task_id for t in PACK.tasks if t.task_id in wind.task_ids()] == [STORM_TASK, BUST_TASK]
    written = snapshot(out)
    assert sorted(written) == sorted(["README.md", "artifacts/portsim-live-verifier/verify.py",
                                      *(f"tasks/{n}.json" for n in names)])
    assert written["artifacts/portsim-live-verifier/verify.py"] == LIVE_BUNDLE.joinpath(
        "artifacts/portsim-live-verifier/verify.py").read_bytes()
    assert written["README.md"].decode() == (
        "PortSim wind dock-v1-eval: 2 weeks, each played in watches by the portsim-llm agent on portsim-wind, with the "
        "port's pilots and tugs in real Barcelona wind and the forecast at every watch, and graded by "
        "portsim-live-verifier.\n\nThe prompts are derived from PortSimEnv's dock-v1 task packs (CC BY-SA 4.0). "
        "Contains data from the Port de Barcelona open data portal. Contains modified ECMWF open data (CC BY 4.0, © "
        "ECMWF) and wind windows derived from the Servei Meteorològic de Catalunya's (Meteocat) XEMA station Y7.\n")
    for name in names:
        assert json.loads(written[f"tasks/{name}.json"]) == wind_steps(name)
    parsed = parse_bundle(out)
    check_bundle(resolve_bundle(parsed))
    assert sum(e.kind is BundleKind.TASK for e in parsed.entries) == 2
    tasks.generate("dock-v1-eval", tmp_path / "two", task_ids=[OTHER_TASK, BUST_TASK], episode_cap_usd=0.75,
                   live=True, wind=True)
    assert sorted(p.name for p in (tmp_path / "two/tasks").iterdir()) == [f"{BUST_TASK}.json", f"{OTHER_TASK}.json"]
    assert json.loads((tmp_path / f"two/tasks/{OTHER_TASK}.json").read_text()) == wind_steps(OTHER_TASK, 0.75)


@pytest.mark.parametrize(("args", "out"), [([], "results/bundles/dock-v1-eval-wind"),
                                           (["--live", "--out", "elsewhere"], "elsewhere")])
def test_generate_wind_writes_to_out_or_results_bundles(tmp_path, monkeypatch, args, out):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(portsim, ["tasks", "generate", "--pack", "dock-v1-eval", "--wind", *args])
    assert result.exit_code == 0, result.output
    assert result.output == (f"Wrote 2 tasks into {out}; play one with: agent-env run {out} --task {STORM_TASK} "
                             "--model <litellm model id>\n")
    assert sorted(p.name for p in (tmp_path / out / "tasks").iterdir()) == [f"{STORM_TASK}.json", f"{BUST_TASK}.json"]
    assert json.loads((tmp_path / out / f"tasks/{STORM_TASK}.json").read_text()) == bundled("week")


@pytest.mark.parametrize(("args", "message"), [
    (["--pack", "dock-v1-train", "--wind"], "--wind plays the one-week dock-v1-eval weeks, not dock-v1-train"),
    (["--pack", "dock-v1-eval", "--wind", "--marine"], "--wind and --marine play different envs: pick one")])
def test_generate_wind_takes_only_the_eval_pack_and_not_with_marine(tmp_path, monkeypatch, args, message):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(portsim, ["tasks", "generate", *args])
    assert result.exit_code == 2 and message in result.output
    assert not (tmp_path / "results").exists()


def test_setup_also_registers_portsim_wind_on_the_gateway_with_the_same_image(local_stores, tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "docker").write_text('#!/bin/sh\ncase "$1" in\n  version) echo linux/arm64 ;;\nesac\n')
    (bin_dir / "docker").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin:/bin")
    stored = []

    def put(id, *, description, image_name):
        stored.append(id)
        return DockerImageArtifact.put_tar(id, description=description, image_name=f"localhost:5000/{id}:v1",
                                           tar_gz_object_url="file:///dev/null")

    monkeypatch.setattr(cli.DockerImageArtifact, "put", put)
    result = CliRunner().invoke(portsim, ["setup", "--source", str(ROOT)])
    assert result.exit_code == 0, result.output
    assert stored == ["agentenv-portsim-env"]
    marine_env, wind_env = Env.get("portsim-marine"), Env.get("portsim-wind")
    assert (wind_env.type, wind_env.environment_name, wind_env.env_provider_type) == (
        "mcp_server", "portsim-wind", "gateway")
    assert wind_env.docker_image_artifact.image_name == marine_env.docker_image_artifact.image_name == (
        "localhost:5000/agentenv-portsim-env:v1")
    assert [line for line in result.output.splitlines() if line.startswith("Registered env")] == [
        f"Registered env '{name}' version 1 (image localhost:5000/agentenv-portsim-env:v1)"
        for name in ("portsim", "portsim-wind", "portsim-live", "portsim-marine")]
