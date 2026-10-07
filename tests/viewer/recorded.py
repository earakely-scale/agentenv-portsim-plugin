"""Recorded runs copied unchanged from results/runs: v1 g2 (a scored week, a week with no plan, a retried week) and two
live weeks, one with get_time calls."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "runs"
SONNET, GPT = "anthropic/claude-sonnet-5-5", "openai/gpt-6.1-sol"
LIVE = [("live-sonnet", SONNET, "dock-24B-w06x1-busy-0"), ("live-gpt", GPT, "dock-36A-w06x1-standard-0")]


def scored(run: str, task_id: str) -> dict:
    rows = [json.loads(line) for line in (ROOT / run / "results.jsonl").read_text().splitlines()]
    return next(r for r in rows if r["task_id"] == task_id and r["outcome"] == "scored")


def transcript(run: str, task_id: str) -> dict:
    return json.loads((ROOT / run / scored(run, task_id)["transcript"]).read_text())
