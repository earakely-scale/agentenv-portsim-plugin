"""Score a PortSim episode with the reward the env gave its submitted plan: 0 when nothing was submitted, and no score
when the env has no task loaded, as after a reset or a restart since the load."""

from agentenv_protocol import client


async def verify(mcp_url: str) -> list[dict]:
    episode = (await client.get_data(mcp_url.removesuffix("/mcp"))).parts[0].data
    if episode["task_id"] is None:
        raise RuntimeError("the env has no task loaded: it was reset or restarted since the load, so the run can't be "
                           "scored")
    reward = episode["reward"] or 0.0
    return [{"criterion": "the submitted plan's reward, 1.0 at the CP-SAT optimum", "result": reward >= 1.0,
             "score": reward, "episode": episode}]
