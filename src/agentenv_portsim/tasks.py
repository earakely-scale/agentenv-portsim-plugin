"""`agent-env portsim tasks`: a task pack as a folder bundle, one task per PortSim task, each played by portsim-llm with
upstream's prompts and limits and graded by portsim-verifier; with --live, the qualifying one-week eval weeks played
live on portsim-live and graded by portsim-live-verifier; with --marine, the qualifying marine weeks played on
portsim-marine with the port's pilots and tugs."""

import json
from importlib.resources import files
from pathlib import Path

import click
from berth_core import Task, TaskPack, rules, situation

from . import marine as marine_weeks
from .schedule import (
    END_WEEK_URI,
    LIVE_ENV,
    LIVE_LOAD_URI,
    MARINE_ENV,
    MAX_TURNS,
    NOTICE_TOOL,
    PLANNING_CALLS,
    schedule,
    triggers,
)
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


HF_BILL_TO_HELP = ("Bill the agent's Hugging Face router calls to this organization (X-HF-Bill-To) instead of the "
                   "token's own account.")


def pack_tasks(name: str) -> list[Task]:
    return TaskPack(PACKS / name).tasks


def agent_env_vars(episode_cap_usd: float, hf_bill_to: str | None) -> dict[str, str]:
    return {"PORTSIM_MAX_COST_USD": format(episode_cap_usd, "g"), **({"HF_BILL_TO": hf_bill_to} if hf_bill_to else {})}


def steps(task: Task, episode_cap_usd: float, hf_bill_to: str | None = None) -> list[dict]:
    return [
        {"id": "deploy", "type": "deploy_env", "env_id": "portsim"},
        {"id": "load-task", "type": "apply_server_config", "env_id": "portsim",
         "directives": [{"service": "portsim", "uri": "urn:portsim:load-task/v1", "args": {"task_id": task.task_id}}]},
        {"id": "deploy-agent", "type": "deploy_agent", "a2a_agent_id": "portsim-llm", "env_ids": ["portsim"],
         "env_vars": agent_env_vars(episode_cap_usd, hf_bill_to)},
        {"id": "play", "type": "prompt_agent", "prompt_id": task.task_id,
         "system_prompt": rules(task, MAX_CHECKS), "prompt": OPENING.format(situation=situation(task)),
         "max_turns": 12, "model_params": {"max_tokens": 32000}, "timeout_seconds": 7200},
        {"id": "grade", "type": "env_outcome_verifier", "env_id": "portsim", "file_artifact_id": "portsim-verifier",
         "verifier_id": "portsim", "score_aggregator": "weighted_average"},
    ]


def live_rules(task: Task) -> str:
    return rules(task, PLANNING_CALLS).split("\n\nTools:\n")[0] + "\n\n" + LIVE_RULES


def live_steps(task: Task, episode_cap_usd: float, hf_bill_to: str | None = None, *, env: str = LIVE_ENV,
               week: type[Week] = Week) -> list[dict]:
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
         "env_vars": agent_env_vars(episode_cap_usd, hf_bill_to)},
        {"id": "clock", "type": "sync_env_clock", "env_id": env, "virtual_time": task.week_start_utc,
         "virtual_seconds_per_real_second": 0, "tolerate_missing_sync_time": False},
        {"id": "play", "type": "prompt_agent", "prompt_id": task.task_id, "system_prompt": live_rules(task),
         "prompt": LIVE_OPENING.format(situation=week(task).situation()["situation"]), "max_turns": MAX_TURNS,
         "model_params": {"max_tokens": 32000}, "timeout_seconds": 7200},
        {"id": "end-week", "type": "apply_server_config", "env_id": env,
         "directives": [{"service": env, "uri": END_WEEK_URI, "args": {}}]},
        {"id": "grade", "type": "env_outcome_verifier", "env_id": env, "file_artifact_id": "portsim-live-verifier",
         "verifier_id": "portsim", "score_aggregator": "weighted_average"},
    ]


def live_references() -> list[dict]:
    return [json.loads(line) for line in REFERENCES.read_text().splitlines()]


def live_task_ids() -> list[str]:
    """The weeks a rolling re-planner on the week as known brings to the hindsight optimum, so 1.0 is reachable live."""
    return [r["task_id"] for r in live_references() if r["qualifies"]]


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def generate(pack: str, out: Path, *, task_ids: list[str] | None = None, episode_cap_usd: float = 5.0,
             live: bool = False, marine: bool = False, hf_bill_to: str | None = None) -> list[str]:
    """Writes the bundle into ``out``: README.md, the verifier and tasks/<task_id>.json, for ``task_ids`` or the whole
    pack (live: the qualifying weeks; marine: the qualifying marine weeks, played live), in the pack's order."""
    live = live or marine
    if live and task_ids is None:
        task_ids = marine_weeks.task_ids() if marine else live_task_ids()
    chosen = [t for t in (marine_weeks.pack().tasks if marine else pack_tasks(pack))
              if task_ids is None or t.task_id in task_ids]
    if marine:
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
        task_steps = (live_steps(task, episode_cap_usd, hf_bill_to, env=MARINE_ENV, week=marine_weeks.MarineWeek)
                      if marine else (live_steps if live else steps)(task, episode_cap_usd, hf_bill_to))
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
@click.option("--out", type=click.Path(file_okay=False, path_type=Path),
              help="The bundle folder to write. Default: results/bundles/<pack>, or <pack>-live with --live, or "
                   "<pack>-marine with --marine.")
@click.option("--hf-bill-to", metavar="ORG", help=HF_BILL_TO_HELP)
def generate_command(pack: str, live: bool, marine: bool, out: Path | None, hf_bill_to: str | None):
    """Write a bundle with one task per task in the pack: deploy the env, load the task, play it with portsim-llm on
    upstream's prompts and limits, and grade it with portsim-verifier. With --live, one task per qualifying week: load
    it into portsim-live, play it in watches, end the week and grade it with portsim-live-verifier. With --marine, the
    same on portsim-marine, with the port's pilots and tugs."""
    if (live or marine) and pack != LIVE_PACK:
        raise click.UsageError(f"{'--marine' if marine else '--live'} plays the one-week {LIVE_PACK} weeks, not {pack}")
    out = out or Path("results/bundles") / (f"{pack}-marine" if marine else f"{pack}-live" if live else pack)
    names = generate(pack, out, live=live, marine=marine, hf_bill_to=hf_bill_to)
    click.echo(f"Wrote {len(names)} tasks into {out}; play one with: agent-env run {out} --task {names[0]} "
               "--model <litellm model id>")
