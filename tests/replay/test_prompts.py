"""Each generated eval task prompts the agent exactly as the 300 published episodes were prompted: its system prompt is
the recorded system message and its prompt the recorded first user message."""

import json

from agentenv_portsim import tasks


def test_the_generated_prompts_are_the_recorded_ones(episodes):
    by_id = {t.task_id: t for t in tasks.pack_tasks("dock-v1-eval")}
    differs = []
    for episode in episodes:
        messages = json.loads(episode["messages"])
        play = next(s for s in tasks.steps(by_id[episode["task_id"]], 5.0) if s["id"] == "play")
        if (play["system_prompt"], play["prompt"]) != (messages[0]["content"], messages[1]["content"]):
            differs.append((episode["model"], episode["task_id"]))
    assert len(episodes) == 300
    assert differs == []
