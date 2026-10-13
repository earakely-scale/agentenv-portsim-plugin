"""`agent-env portsim tasks`: a task pack as a folder bundle, one task per PortSim task, each played by portsim-llm with
upstream's prompts and limits and graded by portsim-verifier; with --live, the qualifying one-week eval weeks played
live on portsim-live and graded by portsim-live-verifier; with --marine, the qualifying marine weeks played on
portsim-marine with the port's pilots and tugs; with --wind, the qualifying wind weeks played on portsim-wind in real
Barcelona wind, with the forecast at every watch; with --lines, the qualifying lines weeks played on portsim-lines, with
each ship's agent deployed as its own A2A agent the planner can message."""

import json
from importlib.resources import files
from pathlib import Path

import click
from berth_core import Task, TaskPack, situation
from berth_core import rules as berth_rules

from . import lines as lines_weeks
from . import marine as marine_weeks
from . import wind as wind_weeks
from .schedule import (
    END_WEEK_URI,
    LINE_AGENT,
    LINE_ROLE,
    LINE_TOOLS,
    LINES_ENV,
    LINES_MAX_TURNS,
    LIVE_ENV,
    LIVE_LOAD_URI,
    MARINE_ENV,
    MAX_TURNS,
    NOTICE_TOOL,
    PLANNING_CALLS,
    WIND_ENV,
    WIND_MAX_TURNS,
    schedule,
    triggers,
)
from .wind import WindWeek
from .world import Week

PACKS = files("agentenv_portsim") / "data"
PACK_NAMES = ["dock-v1-eval", "dock-v1-train"]
LIVE_PACK = "dock-v1-eval"
VERIFIER = files("agentenv_portsim.bundles") / "portsim/artifacts/portsim-verifier/verify.py"
LIVE_VERIFIER = files("agentenv_portsim.bundles") / "portsim-live/artifacts/portsim-live-verifier/verify.py"
REFERENCES = PACKS / "live/references.jsonl"
MAX_CHECKS = 10
OPENING = ("{situation}\n\nMake the new berth plan. Use check_plan to test drafts, then call submit_plan with your "
           "final plan.")
LICENCE = ("The prompts are derived from PortSimEnv's dock-v1 task packs (CC BY-SA 4.0). Contains data from the Port de"
           " Barcelona open data portal.")
WIND_CREDIT = ("Contains modified ECMWF open data (CC BY 4.0, © ECMWF) and wind windows derived from the Servei "
               "Meteorològic de Catalunya's (Meteocat) XEMA station Y7.")
LIVE_OPENING = ("{situation}\n\nIt is watch 0, Monday 00:00. Confirm berth windows with confirm_berths, then call "
                "advance.")
LIVE_RULES = """How the week runs:
- The week is played in watches, starting at watch 0 on Monday 00:00 (hour 0). The table shows the week as the port \
knows it now. News reaches you as messages in tool results: ships report delays and unscheduled calls, the harbour \
master issues gale warnings and emergencies, terminal ops announce closures and crane outages, and the line desk flags \
priority cargo.
- Time only passes when you call advance: the port moves to the next bulletin, ships berth and sail on their confirmed \
windows, and the bulletin's messages arrive with your next tool result. Call advance and get_situation together in one \
turn.
- From watch 1 on, a window that starts before the freeze line (6 hours after the current hour) is frozen: it can't be \
changed, and new or changed windows must start at or after the freeze line. At watch 0 every window is open.
- You have 3 planning calls (check_plan or confirm_berths) per watch.

Tools:
- get_situation(): the hour, the week as known now, your confirmed windows (departed, berthed, frozen or open), the \
ships still without a window, and new messages.
- check_plan(plan): your entries over your confirmed windows, checked on the week as known now: the ships with a \
problem or a cost, the plan's cost, and the entries confirm_berths would refuse. Problems and cost that news brought \
to a frozen window are listed as excused and not counted. It confirms nothing.
- confirm_berths(plan): confirms windows with the ships; ships you leave out keep their windows.
- advance(): ends the watch. After the last watch it returns "done": the rest of the week runs on your confirmed \
windows.

The week is graded once, on the windows you confirmed and the week as it really happened: an infeasible week scores \
low, a feasible one higher the closer its cost is to the best possible in hindsight. Cost or rule breaks that news \
brings to a window that was already frozen are not charged to you. Every ship needs a confirmed window before the week \
ends; if you stop before the last watch, the rest of the week runs on the windows you confirmed."""
WIND_RULES = LIVE_RULES.replace(
    "the harbour master issues gale warnings and emergencies, terminal ops announce closures and crane outages, and "
    "the line desk flags priority cargo.",
    "the harbour master issues emergencies, terminal ops announce closures and crane outages, the line desk flags "
    "priority cargo, and Barcelona Port Control sends the wind forecast at every watch.").replace(
    "the week as it really happened: an infeasible week scores low, a feasible one higher the closer its cost is to "
    "the best possible in hindsight. Cost or rule breaks that news brings to a window that was already frozen are not "
    "charged to you.",
    "the week as it really happened, in the wind that really blew: an infeasible week scores low, a feasible one "
    "higher the closer its cost is to the best possible. Cost or rule breaks that news, or wind the forecast didn't "
    "show, brings to a window after your last chance to change it are not charged to you; wind the forecast showed "
    "then is.")


LINES_RULES = WIND_RULES.replace(
    "ships report delays and unscheduled calls, the harbour master",
    "each ship's agent reports its ETA and calls in before it arrives, the line desk reports unscheduled calls, the "
    "harbour master").replace(
    "Cost or rule breaks that news, or wind the forecast didn't show,",
    "An ETA that proves wrong is not news: a ship that arrives later than its agent said is berthed by the port at "
    "its next free slot, one that arrives earlier waits at anchor for its window, and the lateness and hours at anchor "
    "that follow are charged; a ship whose arrival you agreed arrives at that hour. Cost or "
    "rule breaks that news, or wind the forecast didn't show,").replace(
    "your confirmed windows (departed, berthed, frozen or open),",
    "your confirmed windows (departed, berthed, frozen or open, and where the port berths a ship that gets in after "
    "its window, on its latest ETA until it is in),").replace(
    "- confirm_berths(plan): confirms windows with the ships; ships you leave out keep their windows.",
    "- confirm_berths(plan): confirms windows with the ships; ships you leave out keep their windows. It returns the "
    "confirmed plan's problems and cost, as check_plan does."
) + """

The ships' agents:
- Each ship's agent, the firm that deals with the port for its line, reports the ship's ETA 48 and 24 hours out and \
calls in an hour before the ship arrives. The published schedule is the lines' estimate from about three days out. \
Both are optimistic: most ships arrive later than they say, by less as they near.
- message_agent(agent, requests) sends one agent requests for its ships: {"ship": 7, "ask": "eta", \
"request_arrival": null} for the latest ETA, {"ship": 9, "ask": null, "request_arrival": 130} to ask the ship to \
arrive at that hour. Once the ship has sailed from its previous port or its agent's estimate is within 48 hours, the \
agent agrees \
when it can make the hour at cruising speed or by slowing once it has sailed, and the ship then arrives at that hour; \
otherwise it answers with the earliest or the latest hour the ship can make. Before that, the agent can't commit to \
an hour and gives its ETA.
- Until the port's news about a delayed ship, its agent works from the plan as it stood. The news keeps an earlier \
agreement only if the ship can still make that hour; otherwise the agreement lapses.
- A ship can't berth before it arrives. If it gets in after its window starts, the port berths it at the first hour \
a free stretch of quay fits it, with the same cranes, around every other ship's window and the rules, never ahead of \
an earlier ship whose arrival you agreed still waiting; nothing else moves. A ship that gets in before its window \
waits at anchor for it.
- Ships berth first come, first served: no ship may start berthing while a ship earlier in the queue whose arrival \
you agreed waits at anchor, unless the wind holds that ship or the closures leave no stretch of quay long enough for \
it. A ship's turn is when it would arrive at cruising speed, \
so a ship slowed at your request keeps its turn.
- Each hour a ship waits at anchor between its arrival and its berthing costs its sections, as an hour late does."""
HF_BILL_TO_HELP = ("Bill the agent's Hugging Face router calls to this organization (X-HF-Bill-To) instead of the "
                   "token's own account.")


def pack_tasks(name: str) -> list[Task]:
    return TaskPack(PACKS / name).tasks


def agent_env_vars(episode_cap_usd: float | None, hf_bill_to: str | None) -> dict[str, str]:
    """The agent's environment: a cost cap only when one is asked for (a sweep's), so a published task carries none."""
    return ({"PORTSIM_MAX_COST_USD": format(episode_cap_usd, "g")} if episode_cap_usd is not None else {}) | (
        {"HF_BILL_TO": hf_bill_to} if hf_bill_to else {})


def agent_env(episode_cap_usd: float | None, hf_bill_to: str | None) -> dict[str, dict[str, str]]:
    env = agent_env_vars(episode_cap_usd, hf_bill_to)
    return {"env_vars": env} if env else {}


def steps(task: Task, episode_cap_usd: float | None = None, hf_bill_to: str | None = None) -> list[dict]:
    return [
        {"id": "deploy", "type": "deploy_env", "env_id": "portsim"},
        {"id": "load-task", "type": "apply_server_config", "env_id": "portsim",
         "directives": [{"service": "portsim", "uri": "urn:portsim:load-task/v1", "args": {"task_id": task.task_id}}]},
        {"id": "deploy-agent", "type": "deploy_agent", "a2a_agent_id": "portsim-llm", "env_ids": ["portsim"],
         **agent_env(episode_cap_usd, hf_bill_to)},
        {"id": "play", "type": "prompt_agent", "prompt_id": task.task_id,
         "system_prompt": berth_rules(task, MAX_CHECKS), "prompt": OPENING.format(situation=situation(task)),
         "max_turns": 12, "model_params": {"max_tokens": 32000}, "timeout_seconds": 7200},
        {"id": "grade", "type": "env_outcome_verifier", "env_id": "portsim", "file_artifact_id": "portsim-verifier",
         "verifier_id": "portsim", "score_aggregator": "weighted_average"},
    ]


def live_rules(task: Task, rules: str = LIVE_RULES) -> str:
    return berth_rules(task, PLANNING_CALLS).split("\n\nTools:\n")[0] + "\n\n" + rules


def live_steps(task: Task, episode_cap_usd: float | None = None, hf_bill_to: str | None = None, *, env: str = LIVE_ENV,
               week: type[Week] = Week, rules: str = LIVE_RULES, max_turns: int = MAX_TURNS) -> list[dict]:
    watches = schedule(task)
    return [
        {"id": "deploy", "type": "deploy_env", "env_id": env},
        {"id": "load-task", "type": "apply_server_config", "env_id": env,
         "directives": [{"service": env, "uri": LIVE_LOAD_URI, "args": {"task_id": task.task_id}}]},
        {"id": "hide-port-notice", "type": "modify_env_tool_access", "env_id": env, "action": "disable",
         "role": "default", "tools": [NOTICE_TOOL]},
        {"id": "watches", "type": "register_env_triggers", "env_id": env, "watch_roles": ["default"],
         "triggers": triggers(watches)},
        {"id": "deploy-agent", "type": "deploy_agent", "a2a_agent_id": "portsim-llm", "env_ids": [env],
         **agent_env(episode_cap_usd, hf_bill_to)},
        {"id": "clock", "type": "sync_env_clock", "env_id": env, "virtual_time": task.week_start_utc,
         "virtual_seconds_per_real_second": 0, "tolerate_missing_sync_time": False},
        {"id": "play", "type": "prompt_agent", "prompt_id": task.task_id, "system_prompt": live_rules(task, rules),
         "prompt": LIVE_OPENING.format(situation=week(task).situation()["situation"]), "max_turns": max_turns,
         "model_params": {"max_tokens": 32000}, "timeout_seconds": 7200},
        {"id": "end-week", "type": "apply_server_config", "env_id": env,
         "directives": [{"service": env, "uri": END_WEEK_URI, "args": {}}]},
        {"id": "grade", "type": "env_outcome_verifier", "env_id": env, "file_artifact_id": "portsim-live-verifier",
         "verifier_id": "portsim", "score_aggregator": "weighted_average"},
    ]


def lines_steps(task: Task, episode_cap_usd: float | None = None, hf_bill_to: str | None = None) -> list[dict]:
    """The wind week's steps on portsim-lines, with each firm that has a ship in the week deployed as its own
    portsim-line agent under the line role, which sees only the agents' two tools, and peered with the planner."""
    env, firms = LINES_ENV, sorted(task.rules["lines"]["firms"])
    steps = live_steps(task, episode_cap_usd, hf_bill_to, env=env, week=lines_weeks.LinesWeek, rules=LINES_RULES,
                       max_turns=LINES_MAX_TURNS)
    by_id = {s["id"]: s for s in steps}
    by_id["hide-port-notice"]["tools"] = [NOTICE_TOOL, *LINE_TOOLS]
    by_id["watches"]["triggers"] = triggers(lines_weeks.timetable(task))
    roles = [{"id": "agents-only", "type": "modify_env_tool_access", "env_id": env, "action": "disable",
              "role": LINE_ROLE, "tools": ["*"]},
             {"id": "agents-tools", "type": "modify_env_tool_access", "env_id": env, "action": "enable",
              "role": LINE_ROLE, "tools": list(LINE_TOOLS)}]
    agents = [{"id": f"deploy-{f}", "type": "deploy_agent", "a2a_agent_id": LINE_AGENT, "agent_name": f,
               "role": LINE_ROLE, "env_ids": [env]} for f in firms]
    peers = {"id": "peers", "type": "peer_agents",
             "peerings": [{"source_agent_name": "default-agent", "peer_agent_names": firms}]}
    out = []
    for step in steps:
        out.append(step)
        if step["id"] == "hide-port-notice":
            out += roles
        elif step["id"] == "deploy-agent":
            out += agents + [peers]
    return out


def live_references() -> list[dict]:
    return [json.loads(line) for line in REFERENCES.read_text().splitlines()]


def live_task_ids() -> list[str]:
    """The weeks a rolling re-planner on the week as known brings to the hindsight optimum, so 1.0 is reachable live."""
    return [r["task_id"] for r in live_references() if r["qualifies"]]


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def generate(pack: str, out: Path, *, task_ids: list[str] | None = None, episode_cap_usd: float | None = None,
             live: bool = False, marine: bool = False, hf_bill_to: str | None = None, wind: bool = False,
             lines: bool = False) -> list[str]:
    """Writes the bundle into ``out``: README.md, the verifier and tasks/<task_id>.json, for ``task_ids`` or the whole
    pack (live: the qualifying weeks; marine or wind: the qualifying marine or wind weeks, played live), in the pack's
    order."""
    live = live or marine or wind or lines
    if live and task_ids is None:
        task_ids = (lines_weeks.task_ids() if lines else wind_weeks.task_ids() if wind
                    else marine_weeks.task_ids() if marine else live_task_ids())
    weeks = (lines_weeks.pack().tasks if lines else wind_weeks.pack().tasks if wind
             else marine_weeks.pack().tasks if marine else pack_tasks(pack))
    chosen = [t for t in weeks if task_ids is None or t.task_id in task_ids]
    if lines:
        _write(out / "README.md", f"PortSim lines {pack}: {len(chosen)} weeks, each played in watches by the "
                                  f"portsim-llm agent on portsim-lines, with the wind weeks' pilots, tugs and real "
                                  f"wind, and each ship's agent deployed as a portsim-line agent the planner can "
                                  f"message; graded by portsim-live-verifier.\n\n{LICENCE} {WIND_CREDIT}\n".encode())
    elif wind:
        _write(out / "README.md", f"PortSim wind {pack}: {len(chosen)} weeks, each played in watches by the "
                                  f"portsim-llm agent on portsim-wind, with the port's pilots and tugs in real "
                                  f"Barcelona wind and the forecast at every watch, and graded by "
                                  f"portsim-live-verifier.\n\n{LICENCE} {WIND_CREDIT}\n".encode())
    elif marine:
        _write(out / "README.md", f"PortSim marine {pack}: {len(chosen)} weeks, each played in watches by the "
                                  f"portsim-llm agent on portsim-marine, with the port's pilots and tugs, and graded "
                                  f"by portsim-live-verifier.\n\n{LICENCE}\n".encode())
    elif live:
        _write(out / "README.md", f"PortSim live {pack}: {len(chosen)} weeks, each played in watches by the "
                                  f"portsim-llm agent on portsim-live and graded by portsim-live-verifier.\n\n"
                                  f"{LICENCE}\n".encode())
    else:
        _write(out / "README.md", f"PortSim {pack}: {len(chosen)} tasks, each played by the portsim-llm agent and "
                                  f"graded by portsim-verifier.\n\n{LICENCE}\n".encode())
    if live:
        _write(out / "artifacts/portsim-live-verifier/verify.py", LIVE_VERIFIER.read_bytes())
    else:
        _write(out / "artifacts/portsim-verifier/verify.py", VERIFIER.read_bytes())
    for task in chosen:
        if lines:
            task_steps = lines_steps(task, episode_cap_usd, hf_bill_to)
        elif wind:
            task_steps = live_steps(task, episode_cap_usd, hf_bill_to, env=WIND_ENV, week=WindWeek, rules=WIND_RULES,
                                    max_turns=WIND_MAX_TURNS)
        elif marine:
            task_steps = live_steps(task, episode_cap_usd, hf_bill_to, env=MARINE_ENV, week=marine_weeks.MarineWeek)
        else:
            task_steps = (live_steps if live else steps)(task, episode_cap_usd, hf_bill_to)
        _write(out / "tasks" / f"{task.task_id}.json",
               (json.dumps(task_steps, indent=2, ensure_ascii=False) + "\n").encode())
    return [t.task_id for t in chosen]


@click.group("tasks")
def tasks_group():
    """PortSim tasks for a model: a task pack as a bundle `agent-env run` plays."""


@tasks_group.command("generate")
@click.option("--pack", type=click.Choice(PACK_NAMES), required=True, help="The task pack.")
@click.option("--live", is_flag=True, help=f"Live weeks on portsim-live: the qualifying one-week {LIVE_PACK} weeks.")
@click.option("--marine", is_flag=True,
              help=f"Marine weeks on portsim-marine: the qualifying one-week {LIVE_PACK} weeks with the port's pilots "
                   "and tugs.")
@click.option("--wind", is_flag=True,
              help="Wind weeks on portsim-wind: the qualifying marine weeks moved into real Barcelona wind, with the "
                   "forecast at every watch.")
@click.option("--lines", is_flag=True,
              help="Lines weeks on portsim-lines: the wind weeks with each ship's agent deployed as its own A2A agent, "
                   "ETAs that firm up, requested arrival times and a first-come queue.")
@click.option("--out", type=click.Path(file_okay=False, path_type=Path),
              help="The bundle folder to write. Default: results/bundles/<pack>, or <pack>-live with --live, "
                   "<pack>-marine with --marine, <pack>-wind with --wind, or <pack>-lines with --lines.")
@click.option("--hf-bill-to", metavar="ORG", help=HF_BILL_TO_HELP)
def generate_command(pack: str, live: bool, marine: bool, wind: bool, lines: bool, out: Path | None,
                     hf_bill_to: str | None):
    """Write a bundle with one task per task in the pack: deploy the env, load the task, play it with portsim-llm on
    upstream's prompts and limits, and grade it with portsim-verifier. With --live, one task per qualifying week: load
    it into portsim-live, play it in watches, end the week and grade it with portsim-live-verifier. With --marine, the
    same on portsim-marine, with the port's pilots and tugs. With --wind, the same on portsim-wind, in real Barcelona
    wind with the forecast at every watch. With --lines, the same on portsim-lines, with each ship's agent deployed as a
    portsim-line agent the planner can message."""
    if len(picked := [f for f, on in (("--wind", wind), ("--marine", marine), ("--lines", lines)) if on]) > 1:
        raise click.UsageError(f"{' and '.join(picked)} play different envs: pick one")
    flag = "--lines" if lines else "--wind" if wind else "--marine" if marine else "--live"
    if (live or marine or wind or lines) and pack != LIVE_PACK:
        raise click.UsageError(f"{flag} plays the one-week {LIVE_PACK} weeks, not {pack}")
    out = out or Path("results/bundles") / (f"{pack}-lines" if lines else f"{pack}-wind" if wind
                                             else f"{pack}-marine" if marine else f"{pack}-live" if live else pack)
    names = generate(pack, out, live=live, marine=marine, hf_bill_to=hf_bill_to, wind=wind, lines=lines)
    click.echo(f"Wrote {len(names)} tasks into {out}; play one with: agent-env run {out} --task {names[0]} "
               "--model <litellm model id>")
