"""Recorded runs as PortSimEnv's viewer reads them: a v1 rollout regraded from its final plan, a live week replayed
through its Week, each output as recorded, and the summaries upstream's eval writes."""

import json
import shutil
from dataclasses import fields

import click
import pytest
from recorded import GPT, LIVE, ROOT, SONNET, scored, transcript

from agentenv_portsim import tasks
from agentenv_portsim.episodes import ReplayError, Runs
from agentenv_portsim.schedule import TOOLS, virtual_time
from agentenv_portsim.world import known
from berth_core import Grade

ROLLOUT = {"model", "task_id", "episode_id", "started", "run", "messages", "steps", "final", "reward", "usage", "turns",
           "end_reason", "errors", "seconds"}
SUMMARY = {"model", "task_id", "split", "difficulty", "quay", "ships", "reward", "submitted", "feasible", "cost",
           "optimal_cost", "naive_cost", "turns", "checks", "seconds", "input_tokens", "output_tokens", "end_reason",
           "errors"}
OURS = {"env", "rep", "attempt", "cost_usd"}
LIVE_SUMMARY = {"watches", "confirms", "excused_cost", "regret", "rolling_cost"}
BUSY = "dock-24B-w06x1-busy-0"


def test_a_v1_rollout_is_the_record_with_upstreams_keys_and_its_final_plan_graded(runs):
    ro, row, record = runs.rollout("g2", SONNET, BUSY), scored("g2", BUSY), transcript("g2", BUSY)
    assert set(ro) == ROLLOUT | {"record"}
    assert (ro["messages"], ro["steps"]) == (record["messages"], record["steps"])
    assert (ro["run"], ro["task_id"], ro["episode_id"], ro["started"]) == ("g2", BUSY, "zgbpyyi7", row["started_utc"])
    assert ro["record"] == {"sweep": "g2", "rep": 1, "attempt": 1, "cost_usd": row["cost_usd"],
                            "instance": row["instance"]}
    grade = ro["final"]["grade"]
    assert set(grade) == {f.name for f in fields(Grade)}
    assert grade["reward"] == row["reward"] == record["reward"] == ro["reward"]
    assert grade["cost"] == row["plan_cost"]


def test_a_v1_episode_without_a_plan_has_no_grade_and_its_summary_no_cost(runs):
    task = "dock-36A-w15x2-storm-0"
    assert runs.rollout("g2", SONNET, task)["final"] == {"submitted": False, "plan": None}
    summary = next(e for e in runs.episodes("g2") if e["task_id"] == task)
    assert (summary["submitted"], summary["feasible"], summary["cost"], summary["reward"]) == (False, False, None, 0.0)
    assert summary["end_reason"] == "no_tool_call"


def test_a_retried_week_shows_its_scored_attempt(runs):
    task = "dock-24B-w35x2-storm-0"
    ro = runs.rollout("g2", SONNET, task)
    assert ro["record"]["attempt"] == 2
    assert ro["messages"] == transcript("g2", task)["messages"]
    assert scored("g2", task)["transcript"].endswith("-a2.json")


def test_summaries_carry_upstreams_keys_and_the_attempts_and_a_live_weeks(runs):
    v1 = runs.episodes("g2")
    weeks = [BUSY, "dock-24B-w35x2-storm-0", "dock-36A-w15x2-storm-0"]
    assert [(e["model"], e["task_id"]) for e in v1] == sorted((SONNET, t) for t in weeks)
    assert all(set(e) == SUMMARY | OURS and e["env"] == "portsim" for e in v1)
    [live] = runs.episodes("live-sonnet")
    assert set(live) == SUMMARY | OURS | LIVE_SUMMARY
    ref = next(r for r in tasks.live_references() if r["task_id"] == BUSY)
    assert (live["env"], live["watches"], live["naive_cost"], live["rolling_cost"]) == (
        "portsim-live", len(ref["watch_hours"]), ref["naive"]["cost"], ref["rolling"]["cost"])
    assert live["checks"] + live["confirms"] == scored("live-sonnet", BUSY)["checks"]


@pytest.mark.parametrize(("run", "model", "task_id"), LIVE)
def test_a_live_replay_gives_back_every_recorded_step_and_the_runs_grade(runs, run, model, task_id):
    ro, row, record = runs.rollout(run, model, task_id), scored(run, task_id), transcript(run, task_id)
    assert [(s["turn"], s["tool"], s["entries"]) for s in ro["steps"]] == [
        (s["turn"], s["tool"], s["plan"]) for s in record["steps"]]
    assert [{k: v for k, v in s["result"].items() if k != "violations"} for s in ro["steps"]] == [
        s["result"] for s in record["steps"]]
    grade = ro["final"]["grade"]
    assert (ro["reward"], grade["cost"], grade["excused_cost"], grade["regret"]) == (
        row["reward"], row["plan_cost"], row["excused_cost"], row["regret"])
    assert ro["live"]["audit"] == {"ok": True, "problems": []}
    assert (ro["live"]["end_reason"], ro["final"]["submitted"]) == ("done", True)
    ref = next(r for r in tasks.live_references() if r["task_id"] == task_id)
    assert [w["hour"] for w in ro["live"]["watches"]] == ref["watch_hours"]


@pytest.mark.parametrize(("run", "model", "task_id"), LIVE)
def test_the_trigger_bulletins_are_the_messages_the_agent_got(runs, run, model, task_id):
    ro = runs.rollout(run, model, task_id)
    got = [m for msg in ro["messages"] if msg["role"] == "tool" and msg["name"] in TOOLS
           for m in json.loads(msg["content"]).get("messages", [])]
    assert [(m["hour"], m["from"], m["text"]) for m in got] == [
        (b["hour"], b["from"], b["text"]) for b in ro["live"]["bulletins"] if b["via"] == "trigger"]
    advances = {k for k, s in enumerate(ro["steps"]) if s["tool"] == "advance"}
    assert all(b["step"] in advances and ro["steps"][b["step"]]["watch"] == b["watch"]
               for b in ro["live"]["bulletins"] if b["via"] == "trigger")


@pytest.mark.parametrize(("run", "model", "task_id"), LIVE)
def test_each_step_carries_the_week_as_the_planner_knew_it(runs, run, model, task_id):
    ro, task = runs.rollout(run, model, task_id), runs.pack.get(task_id)
    for step in ro["steps"]:
        assert step["task"] == known(task, step["revealed"]).to_dict(public=True)
        shown = sorted(int(event_id.rsplit("-", 1)[1]) for event_id in step["revealed"])
        assert step["task"]["disruptions"] == [task.disruptions[i] for i in shown]
    assert len(ro["steps"][0]["task"]["disruptions"]) < len(task.disruptions) == len(ro["steps"][-1]["revealed"])


@pytest.mark.parametrize(("run", "model", "task_id"), LIVE)
def test_at_each_advance_the_windows_berth_and_sail_as_the_env_reported(runs, run, model, task_id):
    for step in runs.rollout(run, model, task_id)["steps"]:
        if step["tool"] == "advance" and not step["result"].get("done"):
            for status in ("berthed", "departed"):
                assert [w["ship"] for w in step["windows"] if w["status"] == status] == step["result"][status]


def test_get_time_reads_the_virtual_clock_of_the_last_step(runs):
    ro = runs.rollout("live-gpt", GPT, "dock-36A-w06x1-standard-0")
    steps = {s["call_id"]: s for s in ro["steps"]}
    now = virtual_time(runs.pack.get(ro["task_id"]), 0)
    read = []
    for m in ro["messages"]:
        if m["role"] == "tool" and m["tool_call_id"] in steps:
            now = steps[m["tool_call_id"]]["virtual_time"]
        elif m["role"] == "tool" and m["name"] == "get_time":
            read.append((json.loads(m["content"])["current_time"], now))
    assert len(read) == 3
    assert all(got == expected for got, expected in read)


def test_a_week_the_agent_left_early_runs_on_as_end_week_runs_it(runs):
    messages = transcript("live-sonnet", BUSY)["messages"]
    second = [i for i, m in enumerate(messages) if any(c["name"] == "advance" for c in m.get("tool_calls") or [])][1]
    live = runs.live(runs.pack.get(BUSY), messages[:second])
    assert (live["live"]["end_reason"], live["final"]["submitted"]) == ("end_week", False)
    filled = [b for b in live["live"]["bulletins"] if b["via"] == "env"]
    assert filled and all(b["step"] == len(live["steps"]) - 1 for b in filled)
    assert live["live"]["audit"]["ok"]
    assert live["reward"] == live["final"]["grade"]["reward"]


def test_an_output_the_week_does_not_give_back_stops_the_replay(runs):
    messages = transcript("live-sonnet", BUSY)["messages"]
    i = next(i for i, m in enumerate(messages) if m.get("name") == "check_plan")
    tampered = [*messages[:i], messages[i] | {"content": messages[i]["content"].replace('"cost":15', '"cost":14')},
                *messages[i + 1:]]
    with pytest.raises(ReplayError, match="check_plan"):
        runs.live(runs.pack.get(BUSY), tampered)


def test_a_sweep_of_several_reps_is_a_run_per_rep(tmp_path):
    shutil.copytree(ROOT / "g2", tmp_path / "g2")
    spec = tmp_path / "g2/sweep.json"
    spec.write_text(json.dumps(json.loads(spec.read_text()) | {"k": 2}))
    runs = Runs(tmp_path)
    assert sorted(runs.runs) == ["g2.r1", "g2.r2"]
    assert [r["run"] for r in runs.index()] == ["g2.r1"]
    assert runs.rollout("g2.r1", SONNET, BUSY)["run"] == "g2.r1"


def test_an_unknown_sweep_is_a_usage_error():
    with pytest.raises(click.UsageError, match="no sweep 'nope'"):
        Runs(ROOT, ["nope"])
