"""Record what upstream PortSimEnv v1's harness sends the model in five published episodes: tests/golden/harness.json.

Each episode runs upstream's run_episode against tests/fake_litellm.py, which plays the episode's recorded turns back,
with upstream's env stepped in this process; tests/replay/test_harness.py checks that portsim-llm sends the same
requests. Run it with upstream's code at b0f4c2f in a venv of its own:

    git clone https://github.com/adithya-s-k/FineEnvs && git -C FineEnvs checkout b0f4c2f
    PS=FineEnvs/07-simulation-environments/portsim-v1/envs/berth_planning
    uv venv /tmp/portsim-harness --python 3.12
    uv pip install --python /tmp/portsim-harness/bin/python $PS/core $PS/openenv fastmcp==3.4.8 pydantic==2.13.5 \\
        mcp==1.30.0 anthropic==1.11.0 openai==2.54.0 starlette uvicorn pyarrow huggingface_hub
    PYTHONPATH=tests BERTH_TASKS_DIR=data/dock-v1-eval:data/dock-v1-train \\
        /tmp/portsim-harness/bin/python scripts/record_harness.py
"""

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pyarrow.parquet as pq
from berth_openenv import agent as harness
from berth_openenv.environment import BerthPlanningEnvironment
from fake_litellm import FakeLiteLLM, digest, hf_turns
from huggingface_hub import hf_hub_download
from openenv.core.env_server.mcp_types import ListToolsAction

OUT = Path(__file__).resolve().parents[1] / "tests" / "golden" / "harness.json"
DATASET, REVISION = "FineEnvs/PortSimEnv", "5304899c94f5fbe16b7c6b7fbce98fd90dc9899b"
EPISODES = [
    ("anthropic:claude-sonnet-5-5", "dock-36A-w15x2-storm-0"),
    ("anthropic:claude-sonnet-5-5", "dock-36A-w05x2-storm-0"),
    ("openai:gpt-6.1-sol", "dock-24B-w35x3-extreme-1"),
    ("hf:zai-org/GLM-5.3-Flash:baseten", "dock-24B-w16x2-extreme-0"),
    ("hf:zai-org/GLM-5.3-Flash:baseten", "dock-24B-w35x2-extreme-0"),
]
KEY = "sk-fake-harness"


class InProcess:
    """The harness's OpenEnv client, stepping the env in this process."""

    def __init__(self, env: BerthPlanningEnvironment):
        self.env = env

    def step(self, action):
        obs = self.env.step(action)
        return SimpleNamespace(observation=obs, done=obs.done, reward=obs.reward)


class LocalSession(harness.EnvSession):
    """The harness's env session on upstream's env in this process: its own reset and tools, its own call."""

    def __init__(self, base_url: str):
        self.env = BerthPlanningEnvironment()
        self.client = InProcess(self.env)

    def reset(self, task_id: str, episode_id: str | None = None) -> dict:
        return dict(self.env.reset(task_id=task_id, episode_id=episode_id).metadata or {})

    @property
    def tools(self):
        return self.env.step(ListToolsAction()).tools

    def close(self):
        pass


def main() -> None:
    path = hf_hub_download(DATASET, "rollouts/eval.parquet", repo_type="dataset", revision=REVISION)
    episodes = {(e["model"], e["task_id"]): e for e in pq.read_table(path).to_pylist()}
    harness.EnvSession = LocalSession
    golden = {}
    for spec, task_id in EPISODES:
        episode = episodes[spec, task_id]
        with FakeLiteLLM(hf_turns(episode)) as fake:
            os.environ.update(ANTHROPIC_BASE_URL=fake.url, ANTHROPIC_API_KEY=KEY, OPENAI_BASE_URL=f"{fake.url}/v1",
                              OPENAI_API_KEY=KEY, HF_ROUTER_URL=f"{fake.url}/v1", HF_TOKEN=KEY)
            record = harness.run_episode(spec, "in-process", task_id, max_turns=12, max_tokens=32000,
                                         wall_clock_s=7200)
        assert record["errors"] == [], record["errors"]
        assert record["messages"] == json.loads(episode["messages"]), f"{spec} {task_id} did not replay"
        golden[f"{spec}|{task_id}"] = {"requests": [{"path": path, "sha256": digest(body)}
                                                    for path, _, body in fake.requests]}
    OUT.write_text(json.dumps(golden, indent=1) + "\n")


if __name__ == "__main__":
    main()
