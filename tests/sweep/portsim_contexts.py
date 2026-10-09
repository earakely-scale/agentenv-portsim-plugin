"""The instance contexts a PortSim run stores, as `Task.run()` stores them (`TaskStepContext.to_safe_dict()`): the
verifier's grade and episode, and the play step's PromptResponse and failures."""

from agent_env.task_step.context import PromptResponse, TaskStepContext


def summary(model: str, end_reason: str = "submitted", reward: float | None = 0.944468, cost: float = 0.224018,
            **fields) -> dict:
    return {"agent": "portsim-llm", "model": model, "route": "messages", "end_reason": end_reason,
            "submitted": end_reason == "submitted", "reward": reward, "turns": 2, "tool_calls": 2, "checks": 1,
            "input_tokens": 25105, "output_tokens": 17392, "cached_tokens": 0, "cache_write_tokens": 0,
            "cost_usd": cost, "max_cost_usd": 5.0, "seconds": 124.5, "error": None} | fields


def episode(task: str, reward: float) -> dict:
    """data/get after a feasible submit, as the verifier reads it."""
    return {"task_id": task, "checks_used": 1, "calls_used": 2, "done": True, "end_reason": "submitted", "plan": [],
            "reward": reward, "grade": {
                "reward": reward, "feasible": True, "clean_fraction": 1.0, "quality": 0.9, "cost": 92,
                "delay_cost": 62, "moves": 1, "naive_cost": 658, "optimal_cost": 87, "violations": [],
                "parse_problems": []}}


def play(task: str, model: str, structured: dict | None, code: str | None = None, message: str | None = None,
         trajectory: str | None = "file:///state/agent-env/object_store/trajectories/play.json") -> PromptResponse:
    return PromptResponse(prompt_id=task, response=f"{code or 'submitted'}: ...",
                          agent_trajectory_object_url=trajectory, model=model,
                          error_type="infra_error" if code else None, error_code=code, error_message=message,
                          agent_session_id="a2a-1", agent_name="portsim-llm", step_id="play",
                          structured_output=structured)


def failure(step_id: str, step_type: str, error: str, error_type: str = "RuntimeError") -> dict:
    return {"step_id": step_id, "step_type": step_type, "error": error, "error_type": error_type,
            "started_at_utc": "2026-10-06T12:00:00+00:00", "duration_seconds": 3.0, "is_fatal": True}


def stored(prompt: PromptResponse | None = None, **metadata) -> dict:
    context = TaskStepContext(prompt_responses=[prompt] if prompt else [], metadata=metadata,
                              instance_id="@local/fake/tasks/t-1")
    return context.to_safe_dict()


def scored(task: str, model: str, reward: float = 0.944468, cost: float = 0.224018, **fields) -> dict:
    data = episode(task, reward)
    return stored(play(task, model, summary(model, reward=reward, cost=cost, **fields)),
                  verifications={"portsim": {"results": [
                      {"criterion": "the submitted plan's reward, 1.0 at the CP-SAT optimum", "result": reward >= 1.0,
                       "score": reward, "episode": data}], "score": reward}})


def agent_failed(task: str, model: str, code: str, cost: float = 0.05) -> dict:
    return stored(play(task, model, summary(model, end_reason=code, reward=None, cost=cost,
                                            error=f"APIStatusError: {code}"),
                       code=code, message=f"{code}: the episode stopped"),
                  failed_steps=[failure("play", "prompt_agent",
                                        f"A2A task failed (error_type=infra_error, error_code={code}): {code}")])


def step_failed(step_id: str, step_type: str) -> dict:
    return stored(failed_steps=[failure(step_id, step_type, f"{step_id} failed: the sandbox did not start")])


def crashed(task: str, model: str) -> dict:
    """The agent failed without a structured output: prompt_agent recorded its response and raised."""
    return stored(play(task, model, None), failed_steps=[
        failure("play", "prompt_agent", "A2A task failed (exception=KeyError): the agent crashed")])


def timed_out() -> dict:
    return stored(failed_steps=[failure("play", "prompt_agent", "no answer in 7200s", "TimeoutError")])
