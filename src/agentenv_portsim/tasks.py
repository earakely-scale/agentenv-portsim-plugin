"""`agent-env portsim tasks`: a task pack as a folder bundle, one task per PortSim task, each played by portsim-llm with
upstream's prompts and limits and graded by portsim-verifier."""

import json
from importlib.resources import files
from pathlib import Path

import click

from berth_core import Task, TaskPack, rules, situation

PACKS = files("agentenv_portsim") / "data"
PACK_NAMES = ["dock-v1-eval", "dock-v1-train"]
VERIFIER = files("agentenv_portsim.bundles") / "portsim/artifacts/portsim-verifier/verify.py"
MAX_CHECKS = 10
OPENING = ("{situation}\n\nMake the new berth plan. Use check_plan to test drafts, then call submit_plan with your "
           "final plan.")
LICENCE = ("The prompts are derived from PortSimEnv's dock-v1 task packs (CC BY-SA 4.0). Contains data from the Port de"
           " Barcelona open data portal.")


def pack_tasks(name: str) -> list[Task]:
    return TaskPack(PACKS / name).tasks


def steps(task: Task, episode_cap_usd: float) -> list[dict]:
    return [
        {"id": "deploy", "type": "deploy_env", "env_id": "portsim"},
        {"id": "load-task", "type": "apply_server_config", "env_id": "portsim",
         "directives": [{"service": "portsim", "uri": "urn:portsim:load-task/v1", "args": {"task_id": task.task_id}}]},
        {"id": "deploy-agent", "type": "deploy_agent", "a2a_agent_id": "portsim-llm", "env_ids": ["portsim"],
         "env_vars": {"PORTSIM_MAX_COST_USD": format(episode_cap_usd, "g")}},
        {"id": "play", "type": "prompt_agent", "prompt_id": task.task_id,
         "system_prompt": rules(task, MAX_CHECKS), "prompt": OPENING.format(situation=situation(task)),
         "max_turns": 12, "model_params": {"max_tokens": 32000}, "timeout_seconds": 7200},
        {"id": "grade", "type": "env_outcome_verifier", "env_id": "portsim", "file_artifact_id": "portsim-verifier",
         "verifier_id": "portsim", "score_aggregator": "weighted_average"},
    ]


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def generate(pack: str, out: Path, *, task_ids: list[str] | None = None, episode_cap_usd: float = 5.0) -> list[str]:
    """Writes the bundle into ``out``: README.md, the verifier and tasks/<task_id>.json, for ``task_ids`` or the whole
    pack, in the pack's order."""
    chosen = [t for t in pack_tasks(pack) if task_ids is None or t.task_id in task_ids]
    _write(out / "README.md", f"PortSim {pack}: {len(chosen)} tasks, each played by the portsim-llm agent and "
                              f"graded by portsim-verifier.\n\n{LICENCE}\n".encode())
    _write(out / "artifacts/portsim-verifier/verify.py", VERIFIER.read_bytes())
    for task in chosen:
        text = json.dumps(steps(task, episode_cap_usd), indent=2, ensure_ascii=False) + "\n"
        _write(out / "tasks" / f"{task.task_id}.json", text.encode())
    return [t.task_id for t in chosen]


@click.group("tasks")
def tasks_group():
    """PortSim tasks for a model: a task pack as a bundle `agent-env run` plays."""


@tasks_group.command("generate")
@click.option("--pack", type=click.Choice(PACK_NAMES), required=True, help="The task pack.")
@click.option("--out", type=click.Path(file_okay=False, path_type=Path),
              help="The bundle folder to write. Default: results/bundles/<pack>.")
def generate_command(pack: str, out: Path | None):
    """Write a bundle with one task per task in the pack: deploy the env, load the task, play it with portsim-llm on
    upstream's prompts and limits, and grade it with portsim-verifier."""
    out = out or Path("results/bundles") / pack
    names = generate(pack, out)
    click.echo(f"Wrote {len(names)} tasks into {out}; play one with: agent-env run {out} --task {names[0]} "
               "--model <litellm model id>")
