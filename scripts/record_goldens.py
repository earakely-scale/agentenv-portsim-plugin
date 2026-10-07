"""Record upstream PortSimEnv v1's answers where the published transcripts never go: tests/golden/upstream.json.

That is the MCP tools/list, the 11th check, the 24-call limit and calls after an episode has ended. Each call steps
upstream's env in this process and upstream's harness (EnvSession.call) reads the output, so errors come out as the
model sees them, {"error": msg}. Run it with upstream's code at b0f4c2f in a venv of its own:

    git clone https://github.com/adithya-s-k/FineEnvs && git -C FineEnvs checkout b0f4c2f
    PS=FineEnvs/07-simulation-environments/portsim-v1/envs/berth_planning
    uv venv /tmp/portsim-upstream --python 3.12
    uv pip install --python /tmp/portsim-upstream/bin/python $PS/core $PS/openenv \\
        fastmcp==3.4.8 pydantic==2.13.5 mcp==1.30.0
    BERTH_TASKS_DIR=data/dock-v1-eval:data/dock-v1-train /tmp/portsim-upstream/bin/python scripts/record_goldens.py
"""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from berth_openenv.agent import EnvSession
from berth_openenv.environment import BerthPlanningEnvironment
from fastmcp import Client

OUT = Path(__file__).resolve().parents[1] / "tests" / "golden" / "upstream.json"
TASK = "dock-24B-w07x1-busy-0"
CHECK = ("check_plan", {"plan": "[]"})
EPISODES = {
    "checks": [("check_plan", {"plan": "{"}), *[("check_plan", {"plan": []})] * 10, ("submit_plan", {"plan": []}),
               ("check_plan", {"plan": []}), ("submit_plan", {"plan": []}), ("get_situation", {})],
    "call_limit": [("get_situation", {}), ("check_plan", {}), ("no_such_tool", {}),
                   ("submit_plan", {"plan": [{"ship": 0}]}), *[CHECK] * 9, *[("check_plan", {})] * 10, CHECK, CHECK,
                   ("submit_plan", {"plan": "[]"}), ("get_situation", {})],
}


class InProcess:
    """The harness's OpenEnv client, stepping the env in this process."""

    def __init__(self, env: BerthPlanningEnvironment):
        self.env = env

    def step(self, action):
        obs = self.env.step(action)
        return SimpleNamespace(observation=obs, done=obs.done, reward=obs.reward)


async def tools() -> list[dict]:
    async with Client(BerthPlanningEnvironment().mcp_server) as client:
        return [t.model_dump(mode="json", by_alias=True, exclude_none=True) for t in await client.list_tools()]


def episode(name: str, calls: list[tuple[str, dict]]) -> dict:
    env = BerthPlanningEnvironment()
    env.reset(task_id=TASK)
    harness = EnvSession.__new__(EnvSession)
    harness.client = InProcess(env)
    recorded, reward = [], None
    for tool, arguments in calls:
        output, done, step_reward, _ = harness.call(tool, arguments)
        if done and reward is None:
            reward = step_reward
        recorded.append({"tool": tool, "arguments": arguments, "output": output, "done": done})
    return {"name": name, "task_id": TASK, "calls": recorded,
            "end": {"checks_used": env.state.checks_used, "calls_used": env.state.tool_calls,
                    "end_reason": env._episode.end_reason, "reward": reward}}


def main() -> None:
    golden = {"source": "FineEnvs 07-simulation-environments/portsim-v1 @ b0f4c2f, by scripts/record_goldens.py",
              "tools": asyncio.run(tools()),
              "episodes": [episode(name, calls) for name, calls in EPISODES.items()]}
    OUT.write_text(json.dumps(golden, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
