"""The live verifier against a stand-in env's data/get, scored the way the env_outcome_verifier step scores it: the
executed week's reward, and no score at all for a week that never finished or broke the reveal schedule."""

import asyncio
import importlib.util
import socket
from contextlib import asynccontextmanager
from importlib.resources import as_file, files

import pytest
import uvicorn
from agent_env.task_step.task_steps.verifiers.scoring import ScoreAggregator, aggregate_score
from agentenv_protocol import AgentEnvEnvironment, DataPart, environment_card, get_data
from live_contexts import week

pytestmark = pytest.mark.anyio
TASK = "dock-24B-w07x1-busy-0"


def load_verifier():
    path = files("agentenv_portsim.bundles").joinpath("portsim-live/artifacts/portsim-live-verifier/verify.py")
    with as_file(path) as path:
        spec = importlib.util.spec_from_file_location("portsim_live_verifier", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


verifier = load_verifier()


@environment_card(name="portsim-live")
class Week(AgentEnvEnvironment):
    def __init__(self, answer: dict):
        self.answer = answer

    @get_data
    async def get(self) -> list[DataPart]:
        return [DataPart(data=self.answer)]


@asynccontextmanager
async def served(env: AgentEnvEnvironment):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(env.create_app().streamable_http_app(), host="127.0.0.1", port=port,
                                           log_level="warning"))
    serving = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.01)
    try:
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        server.should_exit = True
        await serving


@pytest.mark.parametrize(("end_reason", "reward"), [("done", 1.0), ("done", 0.8116), ("end_week", 0.0),
                                                    ("end_week", 0.176471)])
async def test_the_score_is_the_executed_weeks_reward_and_the_validity_row_weighs_nothing(end_reason, reward):
    data = week(TASK, reward=reward, end_reason=end_reason)
    async with served(Week(data)) as mcp_url:
        rows = await verifier.verify(mcp_url)
    assert aggregate_score(rows, ScoreAggregator.WEIGHTED_AVERAGE) == reward
    assert [(r["result"], r["score"], r.get("weight", 1)) for r in rows] == [(reward >= 1.0, reward, 1),
                                                                             (True, 1.0, 0)]
    assert rows[0]["episode"] == data


@pytest.mark.parametrize("fields", [
    {"done": False, "end_reason": None, "grade": None, "reward": None},
    {"audit": {"ok": False, "problems": ["late-4 arrived after the agent's next call in watch 4"]}},
])
async def test_a_week_that_never_finished_or_broke_the_reveal_schedule_is_not_scored(fields):
    async with served(Week(week(TASK) | fields)) as mcp_url:
        with pytest.raises(RuntimeError, match="the week can't be scored: done"):
            await verifier.verify(mcp_url)
