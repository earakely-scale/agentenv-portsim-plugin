"""`agent-env portsim sweep run` with a stand-in `agent-env run`: the rows it records, its spend cap, retries, stops and
resume, and the process each attempt runs in."""

import json
import os
import re
import signal
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from agent_env.config import get_config
from agent_env.store.routing import namespace_routing
from agent_env.task.store import get_task_instance_store, seed_task_instance_context
from agent_env.task_step.context import TaskStepContext
from click.testing import CliRunner
from portsim_contexts import agent_failed, crashed, scored, step_failed, summary, timed_out

from agentenv_portsim import sweep
from agentenv_portsim.cli import portsim

SONNET, GPT = "anthropic/claude-sonnet-5-5", "openai/gpt-6.1-sol"
T1, T2, T3 = "dock-24B-w06x1-busy-0", "dock-24B-w06x1-standard-0", "dock-36A-w35x1-standard-0"
ROW_KEYS = ["sweep", "model", "task_id", "rep", "attempt", "started_utc", "wall_seconds", "exit", "instance", "outcome",
            "failed_step", "error_code", "error", "retryable", "reward", "submitted", "feasible", "plan_cost",
            "optimal_cost", "checks", "calls", "end_reason", "turns", "tool_calls", "input_tokens", "output_tokens",
            "cached_tokens", "cache_write_tokens", "cost_usd", "agent_reward", "transcript"]


def sweep_run(*args: str, name: str = "s"):
    return CliRunner().invoke(portsim, ["sweep", "run", "--name", name, *args])


def rows(name: str = "s") -> list[dict]:
    return sweep.results(Path("results/runs") / name)


def brief(row: dict) -> tuple:
    return row["task_id"], row["attempt"], row["outcome"], row["error_code"], row["cost_usd"], row["retryable"]


def test_the_sweep_runs_agent_env_as_a_module_of_this_python():
    assert sweep.AGENT_ENV == [sys.executable, "-m", "agent_env.cli"]


def test_an_attempt_is_one_row_with_the_grade_the_episode_and_the_agents_summary(fake):
    fake.script({"*": [{"context": scored(T1, SONNET)}]})
    result = sweep_run("--models", SONNET, "--tasks", T1, "--cap-usd", "10")
    assert result.exit_code == 0, result.output
    [row] = rows()
    assert list(row) == ROW_KEYS
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", row.pop("started_utc"))
    assert row.pop("instance").startswith(f"@local/fake/tasks/{T1}-")
    assert row == {
        "sweep": "s", "model": SONNET, "task_id": T1, "rep": 1, "attempt": 1, "wall_seconds": 12.5, "exit": 0,
        "outcome": "scored", "failed_step": None, "error_code": None, "error": None, "retryable": False,
        "reward": 0.944468, "submitted": True, "feasible": True, "plan_cost": 92, "optimal_cost": 87, "checks": 1,
        "calls": 2, "end_reason": "submitted", "turns": 2, "tool_calls": 2, "input_tokens": 25105,
        "output_tokens": 17392, "cached_tokens": 0, "cache_write_tokens": 0, "cost_usd": 0.224018,
        "agent_reward": 0.944468, "transcript": f"transcripts/anthropic-claude-sonnet-5-5/{T1}-r1-a1.json"}
    out = Path("results/runs/s")
    assert json.loads((out / row["transcript"]).read_text())["uri"] == (
        "file:///state/agent-env/object_store/trajectories/play.json")
    log = out / f"logs/anthropic-claude-sonnet-5-5/{T1}-r1-a1.log"
    assert "12.5s, instance @local/fake/tasks/" in log.read_text()
    assert json.loads((out / "sweep.json").read_text()) == {
        "name": "s", "models": [SONNET], "tasks": [T1], "k": 1, "episode_cap_usd": 5.0}
    assert [p.name for p in (out / "bundle/tasks").iterdir()] == [f"{T1}.json"]
    assert result.output.splitlines() == [
        f"start {SONNET} {T1} r1 a1 (spent $0.00 of $10.00)",
        f"done {SONNET} {T1} r1 a1: reward 0.944468 (submitted), $0.2240 (spent $0.22)",
        f"{SONNET}: 1 scored, 0 unscored, 0 not final, of 1 runs; $0.22 spent"]


def test_each_attempt_is_a_fresh_agent_env_run_that_inherits_the_environment(fake, monkeypatch, tmp_path):
    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "patches"))
    fake.script({"*": [{"context": scored(T1, SONNET)}]})
    assert sweep_run("--models", SONNET, "--tasks", T1, "--cap-usd", "10").exit_code == 0
    bundle = str(Path.cwd() / "results/runs/s/bundle")
    started = [c for c in fake.calls() if "start" in c]
    assert [c["argv"] for c in started] == [["run", bundle, "--task", T1, "--dry-run"],
                                            ["run", bundle, "--task", T1, "--model", SONNET]]
    assert {c["pythonpath"] for c in started} == {str(tmp_path / "patches")}


def test_a_failed_dry_run_stops_the_sweep_before_any_attempt(fake, monkeypatch):
    monkeypatch.setenv("FAKE_DRY_RUN_EXIT", "1")
    fake.script({"*": [{"context": scored(T1, SONNET)}]})
    result = sweep_run("--models", SONNET, "--tasks", T1, "--cap-usd", "10")
    assert result.exit_code == 1
    assert f"stopped: the dry run of {T1} exited 1" in result.output
    assert fake.runs() == [] and rows() == []


def test_a_sweep_resumes_its_runs_that_are_not_final_and_refuses_other_settings(fake):
    fake.script({"*": [{"context": scored(T1, SONNET, cost=0.3)}]})
    args = ["--models", SONNET, "--tasks", f"{T1},{T2}", "--episode-cap-usd", "0.5"]
    first = sweep_run(*args, "--cap-usd", "0.6")
    assert first.exit_code == 1
    assert first.output.splitlines()[-1] == ("stopped: another attempt could take the spend past $0.60 ($0.30 spent, "
                                             "$0.50 an attempt at most); 1 runs not final")
    second = sweep_run(*args, "--cap-usd", "5", "--parallel", "2")
    assert second.exit_code == 0, second.output
    third = sweep_run(*args, "--cap-usd", "5")
    assert third.exit_code == 0 and not [line for line in third.output.splitlines() if line.startswith("start")]
    assert [r["task_id"] for r in rows()] == [T1, T2]
    assert [a[a.index("--task") + 1] for a in fake.runs()] == [T1, T2]
    for other in (["--models", GPT, "--tasks", f"{T1},{T2}", "--episode-cap-usd", "0.5"],
                  ["--models", SONNET, "--tasks", T1, "--episode-cap-usd", "0.5"],
                  [*args, "--k", "2"], ["--models", SONNET, "--tasks", f"{T1},{T2}"]):
        refused = sweep_run(*other, "--cap-usd", "5")
        assert refused.exit_code == 2 and "is another sweep" in refused.output


def test_failures_are_retried_twice_a_capped_episode_is_final_and_a_deploy_failure_costs_nothing(fake):
    fake.script({
        f"{SONNET}|{T1}": [{"context": agent_failed(T1, SONNET, "provider_error"), "exit": 1}],
        f"{SONNET}|{T2}": [{"context": agent_failed(T2, SONNET, "cost_cap", cost=0.49), "exit": 1}],
        f"{SONNET}|{T3}": [{"context": step_failed("deploy", "deploy_env"), "exit": 1},
                           {"context": scored(T3, SONNET)}],
    })
    result = sweep_run("--models", SONNET, "--tasks", f"{T1},{T2},{T3}", "--cap-usd", "10", "--episode-cap-usd",
                       "0.5", "--parallel", "1")
    assert result.exit_code == 0, result.output
    assert [brief(r) for r in rows()] == [
        (T1, 1, "failed", "provider_error", 0.05, True), (T2, 1, "failed", "cost_cap", 0.49, False),
        (T3, 1, "failed", "RuntimeError", 0.0, True), (T1, 2, "failed", "provider_error", 0.05, True),
        (T3, 2, "scored", None, 0.224018, False), (T1, 3, "failed", "provider_error", 0.05, False)]
    first, _, deploy, *_ = rows()
    assert (first["failed_step"], first["error"], first["end_reason"]) == (
        "play", "provider_error: the episode stopped", "provider_error")
    assert (deploy["failed_step"], deploy["error"], deploy["transcript"]) == (
        "deploy", "deploy failed: the sandbox did not start", None)
    assert f"failed {SONNET} {T1} r1 a1: provider_error retry ($0.0500)" in result.output
    assert f"failed {SONNET} {T2} r1 a1: cost_cap final ($0.4900)" in result.output
    assert f"failed {SONNET} {T1} r1 a3: provider_error final ($0.0500)" in result.output
    assert f"{SONNET}: 1 scored, 2 unscored, 0 not final, of 3 runs; $0.86 spent" in result.output


@pytest.mark.parametrize(("context", "code"), [(None, "no_instance"), (timed_out(), "TimeoutError"),
                                               (crashed(T1, SONNET), "RuntimeError")])
def test_a_run_without_a_recorded_spend_is_retried_and_counted_at_the_cap(fake, context, code):
    fake.script({"*": [{"context": context, "exit": 1}]})
    result = sweep_run("--models", SONNET, "--tasks", f"{T1},{T2},{T3}", "--cap-usd", "1.4", "--episode-cap-usd",
                       "0.5", "--parallel", "1")
    assert result.exit_code == 1
    assert [brief(r) for r in rows()] == [(T1, 1, "failed", code, None, True), (T2, 1, "failed", code, None, True)]
    assert f"failed {SONNET} {T1} r1 a1: {code} retry (no spend recorded, counted as $0.50)" in result.output
    assert result.output.splitlines()[-1].startswith("stopped: another attempt could take the spend past $1.40 "
                                                     "($1.00 spent")


@pytest.mark.parametrize("code", ["model_endpoint", "unpriced_model"])
def test_a_missing_endpoint_or_price_starts_nothing_new_and_lets_running_attempts_finish(fake, code):
    fake.script({f"{SONNET}|{T1}": [{"context": agent_failed(T1, SONNET, code, cost=0.0), "exit": 1}],
                 "*": [{"context": scored(T2, SONNET), "sleep": 0.5}]})
    result = sweep_run("--models", SONNET, "--tasks", f"{T1},{T2},{T3}", "--cap-usd", "10", "--parallel", "2")
    assert result.exit_code == 1
    assert [brief(r) for r in rows()] == [(T1, 1, "failed", code, 0.0, True), (T2, 1, "scored", None, 0.224018, False)]
    assert result.output.splitlines()[-1] == (f"stopped: {code} from {SONNET} {T1} r1 a1: {code}: the episode "
                                              "stopped")


def test_a_signal_tears_the_attempts_down_and_their_rows_dont_count(fake, monkeypatch):
    fake.script({"*": [{"wait": True, "context": scored(T1, SONNET, cost=0.1) | {"metadata": {}}}]})
    sleep, sent = time.sleep, []

    def interrupt(seconds):
        if fake.runs() and not sent:
            sent.append(os.kill(os.getpid(), signal.SIGINT))
        sleep(seconds)

    monkeypatch.setattr(sweep.time, "sleep", interrupt)
    result = sweep_run("--models", SONNET, "--tasks", T1, "--cap-usd", "10")
    assert result.exit_code == 130
    [row] = rows()
    assert (row["outcome"], row["exit"], row["error_code"], row["cost_usd"], row["retryable"]) == (
        "interrupted", 143, None, 0.1, True)
    assert f"interrupted {SONNET} {T1} r1 a1 ($0.1000)" in result.output
    monkeypatch.setattr(sweep.time, "sleep", sleep)
    fake.script({"*": [{"context": agent_failed(T1, SONNET, "env_error"), "exit": 1}]})
    assert sweep_run("--models", SONNET, "--tasks", T1, "--cap-usd", "10").exit_code == 0
    assert [(r["attempt"], r["outcome"], r["retryable"]) for r in rows()] == [
        (1, "interrupted", True), (2, "failed", True), (3, "failed", True), (4, "failed", False)]


def test_an_attempt_that_ended_before_the_signal_keeps_its_own_row(fake, monkeypatch):
    fake.script({f"{SONNET}|{T1}": [{"context": scored(T1, SONNET)}],
                 "*": [{"context": agent_failed(T2, SONNET, "cost_cap", cost=0.49), "sleep": 0.3, "exit": 1}]})
    read = sweep.context

    def interrupt_once_t2_has_ended(instance):
        if T1 in instance:
            while not [c for c in fake.calls() if "end" in c and T2 in c["argv"]]:
                time.sleep(0.02)
            time.sleep(0.3)
            os.kill(os.getpid(), signal.SIGINT)
        return read(instance)

    monkeypatch.setattr(sweep, "context", interrupt_once_t2_has_ended)
    result = sweep_run("--models", SONNET, "--tasks", f"{T1},{T2}", "--cap-usd", "10", "--parallel", "2")
    assert result.exit_code == 130
    assert [brief(r) for r in rows()] == [(T1, 1, "scored", None, 0.224018, False),
                                          (T2, 1, "failed", "cost_cap", 0.49, False)]


def test_a_sweep_that_fails_tears_its_attempts_down_and_counts_them_at_the_cap(fake, monkeypatch):
    fake.script({f"{SONNET}|{T1}": [{"context": scored(T1, SONNET)}],
                 "*": [{"wait": True, "context": scored(T2, SONNET)}]})

    def unreadable(instance):
        raise RuntimeError("the store is down")

    monkeypatch.setattr(sweep, "context", unreadable)
    result = sweep_run("--models", SONNET, "--tasks", f"{T1},{T2}", "--cap-usd", "10", "--parallel", "2")
    assert str(result.exception) == "the store is down"
    assert [(r["task_id"], r["outcome"], r["exit"], r["cost_usd"], r["retryable"]) for r in rows()] == [
        (T1, "interrupted", 0, None, True), (T2, "interrupted", 143, None, True)]
    assert len([c for c in fake.calls() if "end" in c]) == 2


@pytest.mark.parametrize(("context", "outcome", "cost"), [(scored(T1, SONNET), "scored", 0.224018),
                                                          (None, "interrupted", None)])
def test_an_interrupted_attempt_keeps_a_grade_its_run_recorded(fake, tmp_path, context, outcome, cost):
    log = tmp_path / "attempt.log"
    log.write_text("Cancelling: tearing down 1 run\n")
    if context:
        (fake.root / "instances").mkdir()
        (fake.root / "instances/@local_fake_t-1").write_text(json.dumps(context))
        log.write_text(f"  tasks/{T1}.json v1: cancelled, 80.0s, instance @local/fake/t-1\n")
    attempt = sweep.Attempt((SONNET, T1, 1), 1, "2026-10-06T12:00:00Z", log, SimpleNamespace(returncode=143))
    row = sweep.outcome(sweep.Sweep("s", [SONNET], [T1], 1, 0.5), attempt, [], interrupted=True)
    assert (row["outcome"], row["cost_usd"], row["error_code"], row["retryable"]) == (outcome, cost, None,
                                                                                      outcome != "scored")


def test_attempts_go_model_major_and_never_more_than_parallel_at_once(fake):
    fake.script({"*": [{"context": scored(T1, SONNET, cost=0.01), "sleep": 0.2}]})
    result = sweep_run("--models", f"{SONNET},{GPT}", "--tasks", f"{T1},{T2},{T3}", "--k", "2", "--cap-usd", "10",
                       "--parallel", "2")
    assert result.exit_code == 0, result.output
    starts = [line.split()[1:4] for line in result.output.splitlines() if line.startswith("start ")]
    assert starts == [[m, t, f"r{rep}"] for m in (SONNET, GPT) for rep in (1, 2) for t in (T1, T2, T3)]
    assert len(rows()) == 12
    assert max_in_flight(fake) == 2


def test_the_reservation_starts_only_what_the_cap_covers(fake):
    fake.script({"*": [{"context": scored(T1, SONNET, cost=0.3), "sleep": 0.2}]})
    result = sweep_run("--models", SONNET, "--tasks", f"{T1},{T2},{T3}", "--cap-usd", "1.0", "--episode-cap-usd",
                       "0.5", "--parallel", "3")
    assert result.exit_code == 1
    assert max_in_flight(fake) == 2
    assert [r["task_id"] for r in rows()] == [T1, T2]
    assert sum(r["cost_usd"] for r in rows()) + 0.5 > 1.0


def max_in_flight(fake) -> int:
    events = sorted((c.get("start", c.get("end")), 1 if "start" in c else -1) for c in fake.calls()
                    if "--dry-run" not in c["argv"])
    level = peak = 0
    for _, step in events:
        level += step
        peak = max(peak, level)
    return peak


def test_the_reader_finds_the_instance_and_the_trajectory_a_run_stored(local_stores):
    context = TaskStepContext.from_dict(scored(T1, SONNET))
    instance = f"@local/~/results/runs/s/bundle/tasks/{T1}-abcd1234"
    with namespace_routing():
        get_task_instance_store().upsert_instance(instance, f"@local/~/results/runs/s/bundle/tasks/{T1}", 1, 5)
        seed_task_instance_context(instance, context)
        url = get_config().get_object_store().put("trajectories/t.json", b'{"format": "portsim-rollout"}')
    found = sweep.context(instance)
    assert found["prompt_responses"][0]["structured_output"] == summary(SONNET)
    assert found["metadata"]["verifications"]["portsim"]["score"] == 0.944468
    assert sweep.trajectory(url) == b'{"format": "portsim-rollout"}'


def test_task_ids_are_dock_v1_eval_ids(fake):
    assert len(sweep.task_ids("all")) == 50 and sweep.task_ids("g2") == sweep.G2_TASKS
    assert sweep.task_ids(f"{T2},{T1}") == [T2, T1]
    result = sweep_run("--models", SONNET, "--tasks", f"{T1},dock-24B-w03x2-busy-3", "--cap-usd", "1")
    assert result.exit_code == 2 and "not dock-v1-eval task ids: dock-24B-w03x2-busy-3" in result.output
    assert not Path("results").exists() and not (fake.root / "calls.jsonl").exists()
