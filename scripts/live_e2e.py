"""Play a live week through `agent-env run` with no model spend: the task deploys the env (portsim-live,
portsim-marine or portsim-wind) on the gateway and portsim-llm on local Docker, and tests/fake_litellm.py, on this
machine, answers the agent with a reference policy's turns (the naive online policy, or the stored plans of the rolling
re-planner), at one turn per watch. It fails unless each watch's trigger fired once, the agent never saw port_notice,
every bulletin came with the first tool result after its advance and no other, get_time read the watch's hour and held
still between turns, data/get held the week as played in process, and the week scored the policy's stored reward. On
portsim-marine the opening and every get_situation must also carry the pilots and tugs as the port knows them at that
watch; on portsim-wind the situation in each must end with the pilots and tugs and then the wind as the port knows
them then.

Run it from the checkout after `agent-env portsim setup --agent`, with the dev extra installed:

    PYTHONPATH=tests python scripts/live_e2e.py [--env portsim-marine|portsim-wind] [--task ID] [--policy rolling]
        [--double-advance WATCH] [--out week.json]

The bundle's `week` task plays the default week (on portsim-wind, the first qualifying wind week); another week is
written as a one-task bundle in a temporary folder.
"""

import argparse
import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from berth_core import plan_from_list, plan_to_list
from fake_litellm import FakeLiteLLM

from agentenv_portsim import marine, tasks, wind, world
from agentenv_portsim.schedule import LIVE_ENV, MARINE_ENV, NOTICE_TOOL, WIND_ENV, schedule, virtual_time
from agentenv_portsim.sweep import context, trajectory

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


def policy_rows(task, policy: world.Policy, week: type[world.Week]) -> tuple[list[list[dict]], world.Week]:
    """The windows the policy confirms at each watch, as world.play confirms them, and the week it plays."""
    rows = []

    def recorded(w):
        target = policy(w)
        rows.append([r for r in plan_to_list(target) if w.plan.get(r["ship"]) != target[r["ship"]]])
        return target
    played = world.play(task, recorded, week=week)
    assert played.refusals == []
    return rows, played


def script(rows: list[list[dict]], double: int | None) -> list[dict]:
    """One turn per watch: read the clock, confirm the policy's changes, advance, then read the bulletin and the clock.
    With ``double``, the turn before that watch advances twice, skipping a watch where the policy changes nothing."""
    turns, k = [], 0
    while k < len(rows):
        calls = [("get_time", {})] + ([("confirm_berths", {"plan": rows[k]})] if rows[k] else []) + [("advance", {})]
        if k + 1 == double:
            assert not rows[double], f"the policy changes windows at watch {double}"
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


def pilots_and_tugs(task, watches: list, k: int) -> str:
    return marine.section(world.known(task, [n.event_id for w in watches[:k + 1] for n in w.notices]))


def wind_tail(task, watches: list, k: int) -> str:
    """How the situation at watch k ends on portsim-wind: the pilots and tugs, then the wind, as known then."""
    view = wind.known(task, [n.event_id for w in watches[:k + 1] for n in w.notices])
    return "\n\n" + marine.section(view) + "\n\n" + wind.section(view)


def held(data: dict) -> dict:
    """data/get's week but the call counts, which only the env's middleware makes."""
    return {"plan": data["plan"], "notices": [{k: v for k, v in n.items() if k != "call"} for n in data["notices"]],
            "excused": data["excused"], "refusals": data["refusals"], "grade": data["grade"]}


def check(task, fake: FakeLiteLLM, ctx: dict, env: str, expected: dict, played: world.Week) -> dict:
    watches = schedule(task)
    m = ctx["metadata"]
    v = m["verifications"]["portsim"]
    week = v["results"][0]["episode"]
    response = next(p for p in ctx["prompt_responses"] if p.get("step_id") == "play")
    play = response["structured_output"]
    entry = m["env_trigger_state"][env]
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

    if held(week) != held(json.loads(json.dumps(played.data()))):
        problems.append("data/get differs from the week played in process")
    record = json.loads(trajectory(response["agent_trajectory_object_url"]))
    calls = exchanges(record)
    opening = next(m["content"] for m in record["messages"] if m["role"] == "user")
    if env == MARINE_ENV and pilots_and_tugs(task, watches, 0) not in opening:
        problems.append("the opening lacks the pilots and tugs")
    if env == WIND_ENV and not opening.endswith(tasks.LIVE_OPENING.format(situation=wind_tail(task, watches, 0))):
        problems.append("the opening doesn't end with the pilots and tugs and the wind")
    watch, times, delivered, due = 0, {}, [], []
    for name, result in calls:
        if name == "get_time":
            times.setdefault(watch, []).append(result["current_time"])
            continue
        if (name == "get_situation" and env == MARINE_ENV
                and not result["situation"].endswith("\n\n" + pilots_and_tugs(task, watches, watch))):
            problems.append(f"get_situation in watch {watch} lacks the pilots and tugs as known then")
        if (name == "get_situation" and env == WIND_ENV
                and not result["situation"].endswith(wind_tail(task, watches, watch))):
            problems.append(f"get_situation in watch {watch} doesn't end with the pilots and tugs and the wind as "
                            "known then")
        if result["messages"] != due:
            problems.append(f"{name} in watch {watch} carried {result['messages']}, not {due}")
        if due:
            delivered.append((watch, name, len(due)))
        due = []
        if name == "advance" and "watch" in result:
            watch = result["watch"]
            due = [{"hour": watches[watch].hour, "from": n.name, "text": n.text} for n in watches[watch].notices]
    if calls[-1] != ("advance", {"done": True, "feasible": expected["feasible"], "cost": expected["cost"],
                                 "reward": expected["reward"], "messages": []}):
        problems.append(f"the episode ended on {calls[-1]}")
    for k, read in times.items():
        if set(read) != {virtual_time(task, watches[k].hour)}:
            problems.append(f"get_time in watch {k} read {read}, not {virtual_time(task, watches[k].hour)}")
    clock = capture["clock"]
    if clock.get("virtual_seconds_per_real_second") != 0 or clock.get("t0") != virtual_time(task, watches[-1].hour):
        problems.append(f"the clock at the end: {clock}")

    if (v["score"] != expected["reward"] or week["grade"]["cost"] != expected["cost"]
            or week["grade"]["excused_cost"] != expected["excused_cost"] or play["reward"] != expected["reward"]):
        problems.append(f"scored {v['score']} (cost {week['grade']['cost']}, excused {week['grade']['excused_cost']}, "
                        f"agent {play['reward']}); expected {expected['reward']} (cost {expected['cost']}, "
                        f"excused {expected['excused_cost']})")
    if not week["audit"]["ok"] or week["end_reason"] != "done" or play["end_reason"] != "done":
        problems.append(f"audit {week['audit']}, env {week['end_reason']}, agent {play['end_reason']}")
    if len(fake.requests) != play["turns"]:
        problems.append(f"{len(fake.requests)} requests for {play['turns']} turns")
    return {"problems": problems, "score": v["score"], "expected": expected, "fired": fired, "actions": actions,
            "tools": seen, "cache_breakpoints": breakpoints, "bulletins": delivered, "get_time": times,
            "clock": clock, "turns": play["turns"],
            "tool_calls": play["tool_calls"], "cost_usd": play["cost_usd"], "calls_used": week["calls_used"],
            "planning_calls": week["planning_calls"], "frozen_calls": [f["call"] for f in week["frozen"]],
            "notices": [(n["event_id"], n["watch"], n["via"], n["call"]) for n in week["notices"]],
            "data_get_sha256": hashlib.sha256(json.dumps(week, sort_keys=True).encode()).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.partition("\n\n")[0])
    parser.add_argument("--env", choices=[LIVE_ENV, MARINE_ENV, WIND_ENV], default=LIVE_ENV, help="the env to play on")
    parser.add_argument("--task", help="the one-week task to play; default: the bundle's week")
    parser.add_argument("--policy", choices=["naive", "rolling"], default="naive",
                        help="the reference policy the stand-in model plays")
    parser.add_argument("--double-advance", type=int, metavar="WATCH",
                        help="skip this watch with a double advance; the policy must change nothing there")
    parser.add_argument("--out", type=Path, help="write the week's data/get here")
    args = parser.parse_args()
    on_marine, on_wind = args.env == MARINE_ENV, args.env == WIND_ENV
    pack, references, week = ((wind.pack().tasks, wind.references(), wind.WindWeek) if on_wind
                              else (marine.pack().tasks, marine.references(), marine.MarineWeek) if on_marine
                              else (tasks.pack_tasks("dock-v1-eval"), tasks.live_references(), world.Week))
    default = wind.task_ids()[0] if on_wind else TASK
    [task] = [t for t in pack if t.task_id == (args.task or default)]
    reference = next(r for r in references if r["task_id"] == task.task_id)
    plans = reference["rolling"]["plans"]
    policy = world.naive if args.policy == "naive" else lambda w: plan_from_list(plans[w.watch])
    rows, played = policy_rows(task, policy, week)
    turns = script(rows, args.double_advance)
    expected = {k: v for k, v in reference[args.policy].items() if k != "plans"}
    with tempfile.TemporaryDirectory() as tmp:
        bundle, name = args.env, "week"
        if task.task_id != default:
            tasks.generate("dock-v1-eval", Path(tmp), task_ids=[task.task_id], live=True, marine=on_marine,
                           wind=on_wind)
            bundle, name = tmp, task.task_id
        with PausingFake(turns, host="0.0.0.0") as fake:
            port = fake.url.rpartition(":")[2]
            run = subprocess.run([sys.executable, "-m", "agent_env.cli", "run", bundle, "--task", name,
                                  "--model", MODEL], capture_output=True, text=True,
                                 env={**os.environ, "LITELLM_BASE_URL": f"http://host.docker.internal:{port}",
                                      "LITELLM_API_KEY": "sk-fake-live"})
    print(run.stdout + run.stderr)
    instance = re.findall(r"instance (\S+)", run.stdout)
    if not instance:
        sys.exit("the run stored no instance")
    ctx = context(instance[-1])
    report = check(task, fake, ctx, args.env, expected, played)
    if args.out:
        args.out.write_text(json.dumps(ctx["metadata"]["verifications"]["portsim"]["results"][0]["episode"],
                                       indent=2, sort_keys=True) + "\n")
    print(json.dumps({"instance": instance[-1], **report}, indent=1, default=str))
    if report["problems"]:
        sys.exit(f"{len(report['problems'])} problems")


if __name__ == "__main__":
    main()
