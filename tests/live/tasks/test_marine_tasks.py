"""The marine tasks: a marine week's steps against the live week's (portsim-marine, the marine notices on their
watches, the opening with the pilots and tugs), the portsim-marine bundle, `tasks generate --marine`, and `setup`
registering portsim-marine on the gateway."""

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
from berth_core import situation
from click.testing import CliRunner

from agentenv_portsim import cli, marine, tasks, world
from agentenv_portsim.cli import portsim
from agentenv_portsim.marine import MarineWeek
from agentenv_portsim.schedule import schedule

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = files("agentenv_portsim.bundles") / "portsim-marine"
LIVE_BUNDLE = files("agentenv_portsim.bundles") / "portsim-live"
TASK_ID = "dock-24B-w07x1-busy-0"
QUALIFYING = ["dock-24B-w06x1-busy-0", "dock-24B-w07x1-busy-0", "dock-24B-w16x1-busy-0", "dock-24B-w35x1-busy-0",
              "dock-36A-w05x1-busy-0", "dock-36A-w06x1-busy-0", "dock-36A-w17x1-busy-0", "dock-36A-w37x1-busy-0",
              "dock-24B-w06x1-standard-0", "dock-24B-w37x1-standard-0", "dock-36A-w06x1-standard-0",
              "dock-36A-w10x1-standard-0", "dock-36A-w15x1-standard-0", "dock-36A-w35x1-standard-0",
              "dock-36A-w37x1-standard-0"]
WATCHES = [(1, ["extra-1", "tug_outage-8", "pilot_shortage-9"]), (2, ["emergency-7"]), (3, ["late-3"]),
           (4, ["late-4", "crane_outage-6"]), (5, ["gale-0"]), (6, ["bunching-5"])]


def marine_week(task_id: str):
    return marine.pack().get(task_id)


def v2_week(task_id: str):
    return next(t for t in tasks.pack_tasks("dock-v1-eval") if t.task_id == task_id)


def marine_steps(task_id: str, episode_cap_usd: float = 5.0) -> list[dict]:
    return tasks.live_steps(marine_week(task_id), episode_cap_usd, env="portsim-marine", week=MarineWeek)


def on_marine(steps: list[dict]) -> list[dict]:
    """The live week's steps with every env named portsim-marine instead."""
    return json.loads(json.dumps(steps).replace('"portsim-live"', '"portsim-marine"'))


def bundled(name: str) -> list[dict]:
    return json.loads(BUNDLE.joinpath(f"tasks/{name}.json").read_text())


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_a_marine_week_is_the_live_week_on_portsim_marine_with_the_marine_news_and_the_pilots_and_tugs():
    task, steps = marine_week(TASK_ID), marine_steps(TASK_ID)
    live = on_marine(tasks.live_steps(v2_week(TASK_ID), 5.0))
    assert [s["id"] for s in steps] == [s["id"] for s in live]
    assert [s for s in steps if s["id"] not in ("watches", "play")] == [
        s for s in live if s["id"] not in ("watches", "play")]
    assert {s.get("env_id") for s in steps} == {"portsim-marine", None}
    assert steps[1]["directives"][0]["service"] == steps[7]["directives"][0]["service"] == "portsim-marine"
    assert steps[4]["env_ids"] == ["portsim-marine"]
    watches = steps[3]["triggers"]
    assert [(t["id"], [a["args"]["event_id"] for a in t["actions"]]) for t in watches] == [
        (f"watch-{k}", events) for k, events in WATCHES]
    assert [a["args"]["name"] for a in watches[0]["actions"]] == ["MAERSK NUBA", "Tug company", "Pilot station"]
    assert [a["args"]["text"] for a in watches[0]["actions"][1:]] == [
        "2 of the port's 8 tugs are out of service from hour 54 to hour 78: 6 tugs in that window.",
        "2 of the port's 7 pilots on duty are unavailable from hour 54 to hour 66: 5 pilots in that window."]
    [gale] = watches[4]["actions"]
    v2_gale = next(t for t in live if t["id"] == "watches")["triggers"][4]["actions"][0]
    assert gale["args"]["text"] == v2_gale["args"]["text"] + (
        " Ships that berth or leave from hour 115 to hour 144 take one more tug.")
    assert all(a["args"]["text"] == task.notices[int(a["args"]["event_id"].rsplit("-", 1)[1])]
               for t in watches for a in t["actions"])


def test_the_marine_opening_ends_with_the_pilots_and_tugs_and_the_rules_are_the_live_weeks():
    task = marine_week(TASK_ID)
    play = next(s for s in marine_steps(TASK_ID) if s["id"] == "play")
    v2_play = next(s for s in tasks.live_steps(v2_week(TASK_ID), 5.0) if s["id"] == "play")
    view = world.known(task, ["closure-2"])
    assert play["prompt"] == (situation(view) + "\n\n" + marine.section(view) + "\n\nIt is watch 0, Monday 00:00. "
                              "Confirm berth windows with confirm_berths, then call advance.")
    assert play["prompt"].startswith(v2_play["prompt"].removesuffix(
        "\n\nIt is watch 0, Monday 00:00. Confirm berth windows with confirm_berths, then call advance.") + "\n\n")
    assert "- Mon: 745565 266666 764766 354136 | 867675 286888 867888 854765" in play["prompt"].splitlines()
    assert "MAERSK NUBA" not in play["prompt"] and "Tug company" not in play["prompt"]
    assert play["system_prompt"] == v2_play["system_prompt"] == tasks.live_rules(task)
    assert play["max_turns"] == 47 == 5 * len(schedule(marine_week("dock-24B-w16x1-busy-0"))) + 2


def test_the_marine_bundle_installs_week_and_wiring_noplay_and_the_live_verifier(local_stores):
    bundle = checked(find_bundle("portsim-marine"))
    entries = {(e.kind, e.name): e for e in bundle.entries}
    assert bundle.description.startswith(
        "PortSim marine: one week at a Port of Barcelona quay played in watches on the gateway's virtual clock, with "
        "the port's pilots and tugs shared with its other 2024 traffic")
    assert sorted(name for kind, name in entries if kind is BundleKind.TASK) == ["week", "wiring-noplay"]
    assert entries[BundleKind.ARTIFACT, "portsim-live-verifier"].type == "file"
    assert BUNDLE.joinpath("artifacts/portsim-live-verifier/verify.py").read_bytes() == LIVE_BUNDLE.joinpath(
        "artifacts/portsim-live-verifier/verify.py").read_bytes()
    week = marine_steps(TASK_ID)
    assert bundled("week") == week
    assert bundled("wiring-noplay") == [s for s in week if s["id"] not in ("deploy-agent", "play")]
    registry = get_task_step_registry()
    for name in ("week", "wiring-noplay"):
        text = BUNDLE.joinpath(f"tasks/{name}.json").read_text()
        assert text == json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n"
        assert {registry[s["type"]].from_dict(s).env_id for s in bundled(name) if "env_id" in s} == {"portsim-marine"}
    assert len({find_bundle(name).root for name in ("portsim", "portsim-live", "portsim-marine")}) == 3


def test_generate_marine_writes_the_qualifying_marine_weeks_the_live_verifier_and_the_readme(tmp_path, local_stores):
    out = tmp_path / "marine"
    names = tasks.generate("dock-v1-eval", out, marine=True)
    assert names == [t.task_id for t in marine.pack().tasks if t.task_id in marine.task_ids()] == QUALIFYING
    written = snapshot(out)
    assert sorted(written) == sorted(["README.md", "artifacts/portsim-live-verifier/verify.py",
                                      *(f"tasks/{n}.json" for n in names)])
    assert written["artifacts/portsim-live-verifier/verify.py"] == LIVE_BUNDLE.joinpath(
        "artifacts/portsim-live-verifier/verify.py").read_bytes()
    assert written["README.md"].decode() == (
        "PortSim marine dock-v1-eval: 15 weeks, each played in watches by the portsim-llm agent on portsim-marine, "
        "with the port's pilots and tugs, and graded by portsim-live-verifier.\n\nThe prompts are derived from "
        "PortSimEnv's dock-v1 task packs (CC BY-SA 4.0). Contains data from the Port de Barcelona open data portal.\n")
    for name in names:
        assert json.loads(written[f"tasks/{name}.json"]) == marine_steps(name)
    parsed = parse_bundle(out)
    check_bundle(resolve_bundle(parsed))
    assert sum(e.kind is BundleKind.TASK for e in parsed.entries) == 15
    other = "dock-36A-w15x1-busy-0"
    tasks.generate("dock-v1-eval", tmp_path / "two", task_ids=[other, TASK_ID], episode_cap_usd=0.75, live=True,
                   marine=True)
    assert sorted(p.name for p in (tmp_path / "two/tasks").iterdir()) == [f"{TASK_ID}.json", f"{other}.json"]
    assert json.loads((tmp_path / f"two/tasks/{other}.json").read_text()) == marine_steps(other, 0.75)


@pytest.mark.parametrize(("args", "out"), [([], "results/bundles/dock-v1-eval-marine"),
                                           (["--live", "--out", "elsewhere"], "elsewhere")])
def test_generate_marine_writes_to_out_or_results_bundles(tmp_path, monkeypatch, args, out):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(portsim, ["tasks", "generate", "--pack", "dock-v1-eval", "--marine", *args])
    assert result.exit_code == 0, result.output
    assert result.output == (f"Wrote 15 tasks into {out}; play one with: agent-env run {out} --task "
                             "dock-24B-w06x1-busy-0 --model <litellm model id>\n")
    assert sorted(p.name for p in (tmp_path / out / "tasks").iterdir()) == sorted(f"{n}.json" for n in QUALIFYING)
    assert json.loads((tmp_path / out / f"tasks/{TASK_ID}.json").read_text()) == bundled("week")


def test_generate_marine_takes_only_the_eval_pack(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(portsim, ["tasks", "generate", "--pack", "dock-v1-train", "--marine"])
    assert result.exit_code == 2
    assert "--marine plays the one-week dock-v1-eval weeks, not dock-v1-train" in result.output
    assert not (tmp_path / "results").exists()


def test_setup_also_registers_portsim_marine_on_the_gateway_with_the_same_image(local_stores, tmp_path, monkeypatch):
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
    live, marine_env = Env.get("portsim-live"), Env.get("portsim-marine")
    assert (marine_env.type, marine_env.environment_name, marine_env.env_provider_type) == (
        "mcp_server", "portsim-marine", "gateway")
    assert marine_env.docker_image_artifact.image_name == live.docker_image_artifact.image_name == (
        "localhost:5000/agentenv-portsim-env:v1")
    assert result.output.splitlines()[-3:-1] == [
        "Registered env 'portsim-live' version 1 (image localhost:5000/agentenv-portsim-env:v1)",
        "Registered env 'portsim-marine' version 1 (image localhost:5000/agentenv-portsim-env:v1)"]
