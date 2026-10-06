"""The bundle's verifier against a stand-in env's data/get, scored the way the env_outcome_verifier step scores it."""

import asyncio
import importlib.util
import socket
from contextlib import asynccontextmanager
from importlib.resources import as_file, files

import pytest
import uvicorn
from agent_env.task_step.task_steps.verifiers.scoring import ScoreAggregator, aggregate_score
from agentenv_protocol import AgentEnvEnvironment, DataPart, environment_card, get_data

pytestmark = pytest.mark.anyio


def load_verifier():
    with as_file(files("agentenv_portsim.bundles").joinpath("portsim/artifacts/portsim-verifier/verify.py")) as path:
        spec = importlib.util.spec_from_file_location("portsim_verifier", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


verifier = load_verifier()


def episode(**fields) -> dict:
    return {"task_id": "dock-24B-w07x1-busy-0", "checks_used": 0, "calls_used": 0, "done": False, "end_reason": None,
            "plan": None, "grade": None, "reward": None} | fields


@environment_card(name="portsim")
class Episode(AgentEnvEnvironment):
    def __init__(self, answer: dict | Exception):
        self.answer = answer

    @get_data
    async def get(self) -> list[DataPart]:
        if isinstance(self.answer, Exception):
            raise self.answer
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


@pytest.mark.parametrize(("fields", "score"), [
    ({"done": True, "end_reason": "submitted", "reward": 1.0}, 1.0),
    ({"done": True, "end_reason": "submitted", "reward": 0.861234}, 0.861234),
    ({"done": True, "end_reason": "submitted", "reward": 0.176471}, 0.176471),
    ({"done": True, "end_reason": "tool_call_limit", "reward": 0.0}, 0.0),
    ({}, 0.0),
])
async def test_the_score_is_the_reward_of_the_submitted_plan(fields, score):
    async with served(Episode(episode(**fields))) as mcp_url:
        rows = await verifier.verify(mcp_url)
    assert aggregate_score(rows, ScoreAggregator.WEIGHTED_AVERAGE) == score
    assert rows[0]["result"] is (score == 1.0)
    assert rows[0]["episode"] == episode(**fields)


async def test_an_env_that_cannot_report_fails_the_step():
    async with served(Episode(RuntimeError("down"))) as mcp_url:
        with pytest.raises(RuntimeError, match="data/get failed"):
            await verifier.verify(mcp_url)
