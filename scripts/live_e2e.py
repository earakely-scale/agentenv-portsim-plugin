"""Play the portsim-live bundle's week through `agent-env run` with no model spend: the task deploys the env on the
gateway and portsim-llm on local Docker, and tests/fake_litellm.py, on this machine, answers the agent with the naive
online policy's turns, at one turn per watch. It fails unless each watch's trigger fired once, the agent never saw
port_notice, every bulletin came with the first tool result after its advance and no other, get_time read the watch's
hour and held still between turns, and the week scored the stored naive reward.

Run it from the checkout after `agent-env portsim setup --agent`, with the dev extra installed:

    PYTHONPATH=tests python scripts/live_e2e.py [--double-advance WATCH] [--out week.json]
"""

import argparse
import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from fake_litellm import FakeLiteLLM

from agentenv_portsim import tasks, world
from agentenv_portsim.schedule import LIVE_ENV, NOTICE_TOOL, schedule, virtual_time
from agentenv_portsim.sweep import context, trajectory
from berth_core import plan_to_list

TASK = "dock-24B-w07x1-busy-0"
MODEL = "anthropic/claude-sonnet-5-5"
PAUSE = 2.0


class PausingFake(FakeLiteLLM):
    """Answers each request PAUSE seconds late, so real time passes between turns while the clock should not."""

    def _route(self, build):
        endpoint = super()._route(build)

        async def paused(request):
            await asyncio.sleep(PAUSE)
            return await endpoint(request)
        return paused


def naive_rows(task) -> list[list[dict]]:
    """The windows the naive policy confirms at each watch, as world.play confirms them."""
    rows = []

    def policy(week):
        target = world.naive(week)
        rows.append([r for r in plan_to_list(target) if week.plan.get(r["ship"]) != target[r["ship"]]])
        return target
    assert world.play(task, policy).refusals == []
    return rows


def script(rows: list[list[dict]], double: int | None) -> list[dict]:
    """One turn per watch: read the clock, confirm naive's changes, advance, then read the bulletin and the clock.
    With ``double``, the turn before that watch advances twice, skipping a watch where naive changes nothing."""
    turns, k = [], 0
    while k < len(rows):
        calls = [("get_time", {})] + ([("confirm_berths", {"plan": rows[k]})] if rows[k] else []) + [("advance", {})]
        if k + 1 == double:
            assert not rows[double], f"naive changes windows at watch {double}"
            calls.append(("advance", {}))
            k += 1
        if k < len(rows) - 1:
            calls += [("get_situation", {}), ("get_time", {})]
        turns.append({"stop": "tool_use", "tool_calls": [
            {"id": f"toolu_{len(turns)}_{i}", "name": n, "arguments": json.dumps(a)}
            for i, (n, a) in enumerate(calls)]})
        k += 1
    return turns


def exchanges(record: dict) -> list[tuple[str, dict]]:
    """Every tool call of the episode with the result the agent got, from its trajectory."""
    return [(m["name"], json.loads(m["content"])) for m in record["messages"] if m["role"] == "tool"]


def check(task, fake: FakeLiteLLM, ctx: dict) -> dict:
    watches = schedule(task)
    naive = next(r for r in tasks.live_references() if r["task_id"] == task.task_id)["naive"]
    m = ctx["metadata"]
    v = m["verifications"]["portsim"]
    week = v["results"][0]["episode"]
    response = next(p for p in ctx["prompt_responses"] if p.get("step_id") == "play")
    play = response["structured_output"]
    entry = m["env_trigger_state"][LIVE_ENV]
    capture = json.loads(trajectory(entry["object_url"]))
    problems = []

    fired, actions = {}, {}
    for e in capture["state"]["events"]:
        if e["kind"] == "fired":
            fired.setdefault(e["trigger_id"], []).append(e["virtual_time"])
        elif e["kind"] == "action_ok":
            actions.setdefault(e["trigger_id"], []).append(e["detail"]["args"]["event_id"])
    for w in watches[1:]:
        tid, at = f"watch-{w.index}", virtual_time(task, w.hour)
        t = entry["triggers"][tid]
        if (t["status"], t["fire_count"], fired.get(tid)) != ("fired", 1, [at]):
            problems.append(f"{tid}: {t}, fired at {fired.get(tid)}, not once at {at}")
        if actions.get(tid) != [n.event_id for n in w.notices]:
            problems.append(f"{tid} delivered {actions.get(tid)}")

    seen = sorted({tuple(t["name"] for t in body["tools"]) for _, _, body in fake.requests})
    if any(NOTICE_TOOL in names for names in seen):
        problems.append(f"the agent was offered {NOTICE_TOOL}: {seen}")
    breakpoints = [json.dumps(body).count('"cache_control"') for _, _, body in fake.requests]

    calls = exchanges(json.loads(trajectory(response["agent_trajectory_s3_uri"])))
    watch, times, delivered, due = 0, {}, [], []
    for name, result in calls:
        if name == "get_time":
            times.setdefault(watch, []).append(result["current_time"])
            continue
        if result["messages"] != due:
            problems.append(f"{name} in watch {watch} carried {result['messages']}, not {due}")
        if due:
            delivered.append((watch, name, len(due)))
        due = []
        if name == "advance" and "watch" in result:
            watch = result["watch"]
            due = [{"hour": watches[watch].hour, "from": n.name, "text": n.text} for n in watches[watch].notices]
    if calls[-1] != ("advance", {"done": True, "feasible": naive["feasible"], "cost": naive["cost"],
                                 "reward": naive["reward"], "messages": []}):
        problems.append(f"the episode ended on {calls[-1]}")
    for k, read in times.items():
        if set(read) != {virtual_time(task, watches[k].hour)}:
            problems.append(f"get_time in watch {k} read {read}, not {virtual_time(task, watches[k].hour)}")
    clock = capture["clock"]
    if clock.get("virtual_seconds_per_real_second") != 0 or clock.get("t0") != virtual_time(task, watches[-1].hour):
        problems.append(f"the clock at the end: {clock}")

    if v["score"] != naive["reward"] or week["grade"]["cost"] != naive["cost"] or play["reward"] != naive["reward"]:
        problems.append(f"scored {v['score']} (cost {week['grade']['cost']}, agent {play['reward']}); "
                        f"naive {naive['reward']} (cost {naive['cost']})")
    if not week["audit"]["ok"] or week["end_reason"] != "done" or play["end_reason"] != "done":
        problems.append(f"audit {week['audit']}, env {week['end_reason']}, agent {play['end_reason']}")
    if len(fake.requests) != play["turns"]:
        problems.append(f"{len(fake.requests)} requests for {play['turns']} turns")
    return {"problems": problems, "score": v["score"], "naive": naive, "fired": fired, "actions": actions,
            "tools": seen, "cache_breakpoints": breakpoints, "bulletins": delivered, "get_time": times,
            "clock": clock, "turns": play["turns"],
            "tool_calls": play["tool_calls"], "cost_usd": play["cost_usd"], "calls_used": week["calls_used"],
            "planning_calls": week["planning_calls"], "frozen_calls": [f["call"] for f in week["frozen"]],
            "notices": [(n["event_id"], n["watch"], n["via"], n["call"]) for n in week["notices"]],
            "data_get_sha256": hashlib.sha256(json.dumps(week, sort_keys=True).encode()).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.partition("\n\n")[0])
    parser.add_argument("--double-advance", type=int, metavar="WATCH",
                        help="skip this watch with a double advance; naive must change nothing there")
    parser.add_argument("--out", type=Path, help="write the week's data/get here")
    args = parser.parse_args()
    [task] = [t for t in tasks.pack_tasks("dock-v1-eval") if t.task_id == TASK]
    turns = script(naive_rows(task), args.double_advance)
    with PausingFake(turns, host="0.0.0.0") as fake:
        port = fake.url.rpartition(":")[2]
        run = subprocess.run([sys.executable, "-m", "agent_env.cli", "run", LIVE_ENV, "--task", "week",
                              "--model", MODEL], capture_output=True, text=True,
                             env={**os.environ, "LITELLM_BASE_URL": f"http://host.docker.internal:{port}",
                                  "LITELLM_API_KEY": "sk-fake-live"})
    print(run.stdout + run.stderr)
    instance = re.findall(r"instance (\S+)", run.stdout)
    if not instance:
        sys.exit("the run stored no instance")
    ctx = context(instance[-1])
    report = check(task, fake, ctx)
    if args.out:
        args.out.write_text(json.dumps(ctx["metadata"]["verifications"]["portsim"]["results"][0]["episode"],
                                       indent=2, sort_keys=True) + "\n")
    print(json.dumps({"instance": instance[-1], **report}, indent=1, default=str))
    if report["problems"]:
        sys.exit(f"{len(report['problems'])} problems")


if __name__ == "__main__":
    main()
