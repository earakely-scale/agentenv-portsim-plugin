"""G1 (a): the env grades each published final plan to its published reward and grade, and each stored optimal plan
to 1.0."""

import json

from agentenv_portsim.server import PortSimEnv


def test_published_plans(episodes):
    env = PortSimEnv()
    published, graded = {}, {}
    for episode in episodes:
        if episode["submitted"]:
            key = episode["model"], episode["task_id"]
            env.load_task(episode["task_id"])
            env.submit_plan(json.loads(episode["final_plan"]))
            published[key] = episode["reward"], json.loads(episode["grade"])
            graded[key] = env.reward, env.grade
    assert len(published) == 202
    assert {k: (graded[k], v) for k, v in published.items() if graded[k] != v} == {}


def test_optimal_plans():
    env = PortSimEnv()
    rewards = {}
    for task in env.pack.tasks:
        env.load_task(task.task_id)
        env.submit_plan(task.reference["optimal_plan"])
        rewards[task.task_id] = env.reward
    assert len(rewards) == 1100
    assert {task_id: r for task_id, r in rewards.items() if r != 1.0} == {}
