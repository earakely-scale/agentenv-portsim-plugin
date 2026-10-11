"""lines_runs holds a real lines week played on local Docker, each ship's agent a portsim-line agent answering the
planner through the gateway: lines-e2e, the zero-spend end-to-end week of scripts/live_e2e.py (`--env portsim-lines
--policy rolling`), portsim-llm playing the follower's turns from tests/fake_litellm.py under the model id
anthropic/claude-sonnet-5-5. lines_e2e() records it from agent-env's local stores as a sweep records an attempt, with no
wall time, which live_e2e.py doesn't log. A recording replays only on the week it was played on, so a change to the
lines week needs a new end-to-end run and

    PYTHONPATH=tests/viewer .venv/bin/python tests/viewer/lines_recorded.py INSTANCE

to record it."""

import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from agent_env.store.routing import namespace_routing
from agent_env.task.store import get_task_instance_store

from agentenv_portsim import sweep
from agentenv_portsim.schedule import TIME_FORMAT
from agentenv_portsim.sweep import Attempt, Sweep, context, outcome

LINES_ROOT = Path(__file__).resolve().parent / "lines_runs"
E2E_RUN, SONNET = "lines-e2e", "anthropic/claude-sonnet-5-5"
E2E_INSTANCE = "@local/agentenv-portsim/portsim-lines/week-ut5tm7ed"


def started(instance: str) -> str:
    with namespace_routing():
        created = get_task_instance_store().get(instance).created_at_utc
    return datetime.strptime(str(created), "%Y-%m-%d %H:%M UTC").strftime(TIME_FORMAT)


def lines_e2e(root: Path, instance: str = E2E_INSTANCE) -> None:
    """The end-to-end run as a one-attempt lines sweep under ``root``: its row as outcome() reads the instance, its
    transcript the planner's trajectory."""
    task_id = next(p["prompt_id"] for p in context(instance)["prompt_responses"] if p.get("step_id") == "play")
    spec = Sweep(E2E_RUN, [SONNET], [task_id], 1, 5.0, live=True, lines=True)
    out = root / E2E_RUN
    out.mkdir(parents=True, exist_ok=True)
    log = out / "run.log"
    log.write_text(f"0s, instance {instance}\n")
    attempt = Attempt((SONNET, task_id, 1), 1, started(instance), log, SimpleNamespace(returncode=0))
    runs, sweep.RUNS = sweep.RUNS, root
    try:
        row = outcome(spec, attempt, []) | {"wall_seconds": None}
    finally:
        sweep.RUNS = runs
        log.unlink()
    (out / "sweep.json").write_text(json.dumps({k: v for k, v in asdict(spec).items()
                                                if k not in ("live", "marine", "hf_bill_to", "wind", "lines") or v},
                                               indent=2) + "\n")
    (out / "results.jsonl").write_text(json.dumps(row) + "\n")


if __name__ == "__main__":
    lines_e2e(LINES_ROOT, *sys.argv[1:2])
