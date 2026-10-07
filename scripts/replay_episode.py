"""Play a published episode back through `agent-env run` with no model spend: the bundle task deploys the env and
portsim-llm on local Docker, and tests/fake_litellm.py, on this machine, answers the agent with the episode's recorded
turns. It fails unless the task scores the published reward and the agent asked for exactly the recorded turns.

Run it from the checkout after `agent-env portsim setup --agent`, with the dev extra installed:

    PYTHONPATH=tests python scripts/replay_episode.py --bundle results/bundles/dock-v1-eval \\
        --task dock-24B-w06x1-busy-0 --published anthropic:claude-sonnet-5-5 --model anthropic/claude-sonnet-5-5
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import pyarrow.parquet as pq
from fake_litellm import FakeLiteLLM, hf_turns
from huggingface_hub import hf_hub_download

DATASET, REVISION = "FineEnvs/PortSimEnv", "5304899c94f5fbe16b7c6b7fbce98fd90dc9899b"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.partition("\n\n")[0])
    parser.add_argument("--bundle", required=True, type=Path, help="a folder from agent-env portsim tasks generate")
    parser.add_argument("--task", required=True, help="the task id")
    parser.add_argument("--published", required=True, help="the episode's model as published, e.g. openai:gpt-6.1-sol")
    parser.add_argument("--model", required=True, help="the LiteLLM id the agent sends, e.g. openai/gpt-6.1-sol")
    args = parser.parse_args()
    path = hf_hub_download(DATASET, "rollouts/eval.parquet", repo_type="dataset", revision=REVISION)
    [episode] = [e for e in pq.read_table(path).to_pylist()
                 if (e["model"], e["task_id"]) == (args.published, args.task)]
    turns = hf_turns(episode)
    with FakeLiteLLM(turns, host="0.0.0.0") as fake:
        port = fake.url.rpartition(":")[2]
        run = subprocess.run([sys.executable, "-m", "agent_env.cli", "run", str(args.bundle), "--task", args.task,
                              "--model", args.model], capture_output=True, text=True,
                             env={**os.environ, "LITELLM_BASE_URL": f"http://host.docker.internal:{port}",
                                  "LITELLM_API_KEY": "sk-fake-replay"})
    print(run.stdout + run.stderr)
    score = re.search(rf"tasks/{re.escape(args.task)}\.json v\d+: (?:passed|scored below 1) \(grade: ([^)]+)\)",
                      run.stdout)
    if score is None or float(score[1]) != episode["reward"]:
        sys.exit(f"{args.task} scored {score[1] if score else 'nothing'}; published: {episode['reward']}")
    if len(fake.requests) != len(turns):
        sys.exit(f"the agent sent {len(fake.requests)} requests for the {len(turns)} recorded turns")
    print(f"{args.task}, {args.model} replaying {args.published}: {episode['reward']} as published, "
          f"{len(turns)} turns")


if __name__ == "__main__":
    main()
