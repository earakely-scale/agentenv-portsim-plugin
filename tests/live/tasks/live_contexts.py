"""The instance contexts a live PortSim run stores, as `Task.run()` stores them (`TaskStepContext.to_safe_dict()`):
the live verifier's rows and week, and the play step's PromptResponse and failures."""

from agent_env.task_step.context import PromptResponse, TaskStepContext


def week(task: str, reward: float = 1.0, end_reason: str = "done", cost: int = 226, excused: int = 20,
         **fields) -> dict:
    """data/get after a feasible week ended, as the live verifier reads it."""
    return {"task_id": task, "watches": 7, "watch": 6, "hour": 120, "done": True, "end_reason": end_reason,
            "calls_used": 31, "planning_calls": [3, 2, 1, 2, 1, 3, 2],
            "plan": [{"ship": 0, "berth_hour": 1, "section": 2, "cranes": 5}],
            "notices": [{"event_id": "closure-2", "kind": "closure", "name": "Terminal ops", "watch": 0, "hour": 0,
                         "via": "load", "call": 0, "matches": True}],
            "frozen": [{"watch": 0, "hour": 0, "before": 0, "call": 0, "ships": []}], "refusals": [],
            "excused": {"problems": [], "cost": [{"event_id": "gale-0", "ship": 7, "cost": excused}]},
            "audit": {"ok": True, "problems": []},
            "grade": {"reward": reward, "feasible": True, "clean_fraction": 1.0, "quality": reward, "cost": cost,
                      "raw_cost": cost + excused, "excused_cost": excused, "optimal_cost": 226,
                      "unavoidable_cost": 177, "regret": cost - 226, "violations": [], "excused": []},
            "reward": reward} | fields


def summary(model: str, end_reason: str = "done", reward: float | None = 1.0, cost: float = 0.61, **fields) -> dict:
    return {"agent": "portsim-llm", "model": model, "route": "messages", "end_reason": end_reason, "submitted": False,
            "reward": reward, "turns": 30, "tool_calls": 31, "checks": 6, "input_tokens": 412000,
            "output_tokens": 38000, "cached_tokens": 351000, "cache_write_tokens": 40000, "cost_usd": cost,
            "max_cost_usd": 5.0, "seconds": 640.0, "error": None} | fields


def play(task: str, model: str, structured: dict | None) -> PromptResponse:
    return PromptResponse(prompt_id=task, response="done: ...",
                          agent_trajectory_object_url="file:///state/agent-env/object_store/trajectories/play.json",
                          model=model, agent_session_id="a2a-1", agent_name="portsim-llm", step_id="play",
                          structured_output=structured)


def stored(prompt: PromptResponse | None = None, **metadata) -> dict:
    context = TaskStepContext(prompt_responses=[prompt] if prompt else [], metadata=metadata,
                              instance_id="@local/fake/tasks/t-1")
    return context.to_safe_dict()


def scored(task: str, model: str, data: dict, agent: dict) -> dict:
    reward = data["reward"]
    return stored(play(task, model, agent), verifications={"portsim": {"results": [
        {"criterion": "the executed week's reward, 1.0 at the hindsight optimum", "result": reward >= 1.0,
         "score": reward, "episode": data},
        {"criterion": "every watch got its notices, in order, before the agent's next call", "result": True,
         "score": 1.0, "weight": 0}], "score": reward}})


def unscorable(task: str, model: str, agent: dict) -> dict:
    """The live verifier raised: the week never finished or its notices broke the schedule."""
    return stored(play(task, model, agent), failed_steps=[{
        "step_id": "grade", "step_type": "env_outcome_verifier",
        "error": "the week can't be scored: done True, audit {'ok': False, 'problems': ['watch 2 got [] instead of "
                 "['emergency-7']']}", "error_type": "RuntimeError", "started_at_utc": "2026-10-07T12:00:00+00:00",
        "duration_seconds": 1.0, "is_fatal": True}])
