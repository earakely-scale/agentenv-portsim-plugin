"""The live tasks: the exact steps of a live week and its trigger per watch, the portsim-live bundle, `tasks generate
--live`, and `setup` registering portsim-live on the gateway."""

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
from click.testing import CliRunner

from agentenv_portsim import cli, tasks, world
from agentenv_portsim.cli import portsim
from berth_core import rules, situation

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = files("agentenv_portsim.bundles") / "portsim-live"
TASK_ID = "dock-24B-w07x1-busy-0"
LIVE_RULES = "\n".join([
    "How the week runs:",
    "- The week is played in watches, starting at watch 0 on Monday 00:00 (hour 0). The table shows the week as the "
    "port knows it now. News reaches you as messages in tool results: ships report delays and unscheduled calls, the "
    "harbour master issues gale warnings and emergencies, terminal ops announce closures and crane outages, and the "
    "line desk flags priority cargo.",
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
    "The week is graded once, on the windows you confirmed and the week as it really happened: an infeasible week "
    "scores low, a feasible one higher the closer its cost is to the best possible in hindsight. Cost or rule breaks "
    "that news brings to a window that was already frozen are not charged to you. Every ship needs a confirmed window "
    "before the week ends; if you stop before the last watch, the rest of the week runs on the windows you confirmed.",
])
WATCHES = [(1, [("extra-1", "MAERSK NUBA")]), (2, [("emergency-7", "Harbour master")]), (3, [("late-3", "CARLOTA B")]),
           (4, [("late-4", "MAERSK NARMADA"), ("crane_outage-6", "Terminal ops")]),
           (5, [("gale-0", "Harbour master")]), (6, [("bunching-5", "Ship agents")])]


def pack_task(task_id: str):
    return next(t for t in tasks.pack_tasks("dock-v1-eval") if t.task_id == task_id)


def bundled(name: str) -> list[dict]:
    return json.loads(BUNDLE.joinpath(f"tasks/{name}.json").read_text())


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_a_live_week_loads_hides_port_notice_registers_its_watches_arms_the_clock_plays_ends_and_grades():
    task = pack_task(TASK_ID)
    triggers = [{"id": f"watch-{k}",
                 "when": {"type": "action", "tool": "advance", "where": {"result.watch": {"equals": k}}},
                 "barrier": {"at": "provoking_call", "timeout_seconds": 60},
                 "actions": [{"type": "tool", "tool": "port_notice",
                              "args": {"event_id": event, "name": name,
                                       "text": task.notices[int(event.rsplit("-", 1)[1])]}}
                             for event, name in notices]} for k, notices in WATCHES]
    assert tasks.live_steps(task, 5.0) == [
        {"id": "deploy", "type": "deploy_env", "env_id": "portsim-live"},
        {"id": "load-task", "type": "apply_server_config", "env_id": "portsim-live",
         "directives": [{"service": "portsim-live", "uri": "urn:portsim:live-load/v1", "args": {"task_id": TASK_ID}}]},
        {"id": "hide-port-notice", "type": "modify_env_tool_access", "env_id": "portsim-live", "action": "disable",
         "role": "default", "tools": ["port_notice"]},
        {"id": "watches", "type": "register_env_triggers", "env_id": "portsim-live", "watch_roles": ["default"],
         "triggers": triggers},
        {"id": "deploy-agent", "type": "deploy_agent", "a2a_agent_id": "portsim-llm", "env_ids": ["portsim-live"],
         "env_vars": {"PORTSIM_MAX_COST_USD": "5"}},
        {"id": "clock", "type": "sync_env_clock", "env_id": "portsim-live", "virtual_time": "2024-02-12T00:00:00Z",
         "virtual_seconds_per_real_second": 0, "tolerate_missing_sync_time": False},
        {"id": "play", "type": "prompt_agent", "prompt_id": TASK_ID,
         "system_prompt": rules(task, 3).split("\n\nTools:\n")[0] + "\n\n" + LIVE_RULES,
         "prompt": situation(world.known(task, ["closure-2"])) + "\n\nIt is watch 0, Monday 00:00. Confirm berth "
                                                                 "windows with confirm_berths, then call advance.",
         "max_turns": 37, "model_params": {"max_tokens": 32000}, "timeout_seconds": 7200},
        {"id": "end-week", "type": "apply_server_config", "env_id": "portsim-live",
         "directives": [{"service": "portsim-live", "uri": "urn:portsim:end-week/v1", "args": {}}]},
        {"id": "grade", "type": "env_outcome_verifier", "env_id": "portsim-live",
         "file_artifact_id": "portsim-live-verifier", "verifier_id": "portsim", "score_aggregator": "weighted_average"},
    ]
    assert triggers[3]["actions"] == [
        {"type": "tool", "tool": "port_notice", "args": {
            "event_id": "late-4", "name": "MAERSK NARMADA",
            "text": "Ship 10 MAERSK NARMADA was delayed leaving Valencia: it now arrives at hour 129 (planned slot "
                    "hour 112). Its planned departure stays hour 128."}},
        {"type": "tool", "tool": "port_notice", "args": {
            "event_id": "crane_outage-6", "name": "Terminal ops",
            "text": "2 of the terminal's 9 quay cranes are out of service from hour 108 to hour 155 (gantry repair): "
                    "7 cranes in that window."}}]


def test_the_live_prompts_keep_the_rules_and_show_only_the_week_known_at_hour_0():
    task = pack_task(TASK_ID)
    play = next(s for s in tasks.live_steps(task, 5.0) if s["id"] == "play")
    assert tasks.LIVE_RULES == LIVE_RULES
    assert play["system_prompt"].count("Tools:") == 1 and "submit_plan" not in play["system_prompt"]
    assert play["system_prompt"].startswith("You are the berth planner for this quay.")
    opening = play["prompt"].splitlines()
    assert "## Notices" in opening and f"- {task.notices[2]}" in opening
    assert not [n for i, n in enumerate(task.notices) if i != 2 and f"- {n}" in opening]
    assert "| 7 | CARLOTA B | 141 | 4 | 78 | 1204 | 1-2 | 78 @ 4, 1 cranes | 121 |  |" in opening
    assert "| 5 | ZIM CHINA | 261 | 6 | 54 | 840 | 1-5 | 54 @ 4, 3 cranes | 64 |  |" in opening
    assert not [line for line in opening if "MAERSK NUBA" in line]


@pytest.mark.parametrize(("task_id", "turns"), [("dock-36A-w10x1-standard-0", 12), ("dock-24B-w16x1-busy-0", 47)])
def test_a_week_gets_five_turns_a_watch_and_two_more(task_id, turns):
    play = next(s for s in tasks.live_steps(pack_task(task_id), 5.0) if s["id"] == "play")
    assert play["max_turns"] == turns


def test_the_bundle_installs_week_and_wiring_noplay_and_the_live_verifier(local_stores):
    bundle = checked(find_bundle("portsim-live"))
    entries = {(e.kind, e.name): e for e in bundle.entries}
    assert bundle.description.startswith("PortSim live: one week at a Port of Barcelona quay played in watches")
    assert sorted(name for kind, name in entries if kind is BundleKind.TASK) == ["week", "wiring-noplay"]
    assert entries[BundleKind.ARTIFACT, "portsim-live-verifier"].type == "file"
    week = tasks.live_steps(pack_task(TASK_ID), 5.0)
    assert bundled("week") == week
    assert bundled("wiring-noplay") == [s for s in week if s["id"] not in ("deploy-agent", "play")]
    registry = get_task_step_registry()
    for name in ("week", "wiring-noplay"):
        text = BUNDLE.joinpath(f"tasks/{name}.json").read_text()
        assert text == json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n"
        assert {registry[s["type"]].from_dict(s).env_id for s in bundled(name) if "env_id" in s} == {"portsim-live"}
    assert find_bundle("portsim").root != find_bundle("portsim-live").root


def test_generate_live_writes_the_qualifying_weeks_the_live_verifier_and_the_readme(tmp_path, local_stores):
    out = tmp_path / "live"
    names = tasks.generate("dock-v1-eval", out, live=True)
    assert names == [t.task_id for t in tasks.pack_tasks("dock-v1-eval") if t.task_id in tasks.live_task_ids()]
    assert len(names) == 15
    written = snapshot(out)
    assert sorted(written) == sorted(["README.md", "artifacts/portsim-live-verifier/verify.py",
                                      *(f"tasks/{n}.json" for n in names)])
    assert written["artifacts/portsim-live-verifier/verify.py"] == BUNDLE.joinpath(
        "artifacts/portsim-live-verifier/verify.py").read_bytes()
    assert written["README.md"].decode() == (
        "PortSim live dock-v1-eval: 15 weeks, each played in watches by the portsim-llm agent on portsim-live and "
        "graded by portsim-live-verifier.\n\nThe prompts are derived from PortSimEnv's dock-v1 task packs (CC BY-SA "
        "4.0). Contains data from the Port de Barcelona open data portal.\n")
    for name in names:
        assert json.loads(written[f"tasks/{name}.json"]) == tasks.live_steps(pack_task(name), 5.0)
    parsed = parse_bundle(out)
    check_bundle(resolve_bundle(parsed))
    assert sum(e.kind is BundleKind.TASK for e in parsed.entries) == 15
    tasks.generate("dock-v1-eval", tmp_path / "two", task_ids=[names[1], names[0]], episode_cap_usd=0.75, live=True)
    assert sorted((tmp_path / "two/tasks").iterdir()) == [tmp_path / f"two/tasks/{n}.json" for n in names[:2]]
    deploy_agent = json.loads((tmp_path / f"two/tasks/{names[0]}.json").read_text())[4]
    assert deploy_agent["env_vars"] == {"PORTSIM_MAX_COST_USD": "0.75"}


@pytest.mark.parametrize(("args", "out"), [([], "results/bundles/dock-v1-eval-live"), (["--out", "elsewhere"],
                                                                                         "elsewhere")])
def test_generate_live_writes_to_out_or_results_bundles(tmp_path, monkeypatch, args, out):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(portsim, ["tasks", "generate", "--pack", "dock-v1-eval", "--live", *args])
    assert result.exit_code == 0, result.output
    assert result.output.startswith(f"Wrote 15 tasks into {out}; play one with: agent-env run {out} --task ")
    assert len(list((tmp_path / out / "tasks").iterdir())) == 15


def test_generate_live_takes_only_the_eval_pack(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(portsim, ["tasks", "generate", "--pack", "dock-v1-train", "--live"])
    assert result.exit_code == 2
    assert "--live plays the one-week dock-v1-eval weeks, not dock-v1-train" in result.output
    assert not (tmp_path / "results").exists()


def test_setup_also_registers_portsim_live_on_the_gateway_with_the_same_image(local_stores, tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "docker").write_text('#!/bin/sh\ncase "$1" in\n  version) echo linux/arm64 ;;\nesac\n')
    (bin_dir / "docker").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin:/bin")
    stored = []

    def put(id, *, description, image_name):
        stored.append(id)
        return DockerImageArtifact.put_tar(id, description=description, image_name=f"localhost:5000/{id}:v1",
                                           tar_gz_s3_url="file:///dev/null")

    monkeypatch.setattr(cli.DockerImageArtifact, "put", put)
    result = CliRunner().invoke(portsim, ["setup", "--source", str(ROOT)])
    assert result.exit_code == 0, result.output
    assert stored == ["agentenv-portsim-env"]
    v1, live = Env.get("portsim"), Env.get("portsim-live")
    assert (live.type, live.environment_name, live.env_provider_type) == ("mcp_server", "portsim-live", "gateway")
    assert v1.env_provider_type == "server"
    assert live.docker_image_artifact.image_name == v1.docker_image_artifact.image_name == (
        "localhost:5000/agentenv-portsim-env:v1")
    assert "Registered env 'portsim' version 1" in result.output
    assert "Registered env 'portsim-live' version 1 (image localhost:5000/agentenv-portsim-env:v1)" in result.output
