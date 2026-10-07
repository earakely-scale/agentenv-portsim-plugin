"""`agent-env portsim sweep run|report --live`: the live weeks and their order, the live flag in sweep.json and how
older files read, live rows from a stand-in `agent-env run`, and the live report against the rolling and naive
references."""

import json
import sys
import textwrap
from pathlib import Path

import click
import pytest
from click.testing import CliRunner
from live_contexts import scored, summary, unscorable, week

from agentenv_portsim import sweep, tasks
from agentenv_portsim.cli import portsim

SONNET, GPT = "anthropic/claude-sonnet-5-5", "openai/gpt-6.1-sol"
A, B = "dock-36A-w35x1-standard-0", "dock-24B-w07x1-busy-0"
ROW_KEYS = ["sweep", "model", "task_id", "rep", "attempt", "started_utc", "wall_seconds", "exit", "instance", "outcome",
            "failed_step", "error_code", "error", "retryable", "reward", "submitted", "feasible", "plan_cost",
            "optimal_cost", "checks", "calls", "end_reason", "turns", "tool_calls", "input_tokens", "output_tokens",
            "cached_tokens", "cache_write_tokens", "cost_usd", "agent_reward", "transcript", "watches", "excused_cost",
            "regret"]
FAKE = textwrap.dedent("""
    import json, os, sys, uuid
    from pathlib import Path

    here = Path(os.environ["FAKE_AGENT_ENV"])
    args = sys.argv[1:]
    with open(here / "calls.jsonl", "a") as f:
        f.write(json.dumps(args) + "\\n")
    if "--dry-run" in args:
        sys.exit(0)
    task = args[args.index("--task") + 1]
    instance = f"@local/fake/tasks/{task}-{uuid.uuid4().hex[:8]}"
    (here / "instances").mkdir(exist_ok=True)
    script = json.loads((here / "script.json").read_text())
    (here / "instances" / instance.replace("/", "_")).write_text(json.dumps(script[task]))
    print(f"  tasks/{task}.json v1: done, 640.5s, instance {instance}")
""")


@pytest.fixture
def fake(tmp_path, monkeypatch) -> Path:
    """A stand-in `agent-env run` that leaves the context script.json holds for the task where the sweep reads it."""
    root = tmp_path / "fake"
    root.mkdir()
    (root / "agent_env_run.py").write_text(FAKE)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FAKE_AGENT_ENV", str(root))
    monkeypatch.setattr(sweep, "AGENT_ENV", [sys.executable, str(root / "agent_env_run.py")])
    monkeypatch.setattr(sweep, "POLL_SECONDS", 0.02)
    monkeypatch.setattr(sweep, "context",
                        lambda instance: json.loads((root / "instances" / instance.replace("/", "_")).read_text()))
    monkeypatch.setattr(sweep, "trajectory", lambda uri: b"{}")
    return root


def sweep_run(*args: str, name: str = "live"):
    return CliRunner().invoke(portsim, ["sweep", "run", "--live", "--name", name, *args])


def test_the_live_weeks_run_g2_first_then_by_watches_and_a_listed_week_must_be_live():
    watches = {r["task_id"]: len(r["watch_hours"]) for r in tasks.live_references()}
    ids = sweep.task_ids("all", live=True)
    assert sorted(ids) == sorted(tasks.live_task_ids())
    assert ids == ["dock-24B-w06x1-busy-0", "dock-36A-w05x1-busy-0", A, "dock-36A-w10x1-standard-0",
                   "dock-36A-w06x1-standard-0", "dock-24B-w06x1-standard-0", "dock-24B-w37x1-standard-0",
                   "dock-36A-w15x1-standard-0", "dock-36A-w17x1-busy-0", "dock-36A-w37x1-standard-0",
                   "dock-36A-w06x1-busy-0", B, "dock-36A-w37x1-busy-0", "dock-24B-w35x1-busy-0",
                   "dock-24B-w16x1-busy-0"]
    assert [watches[t] for t in ids[3:]] == sorted(watches[t] for t in ids[3:])
    assert sweep.task_ids("g2", live=True) == [A, "dock-24B-w06x1-busy-0", "dock-36A-w05x1-busy-0"]
    assert sweep.task_ids(f"{B},{A}", live=True) == [B, A]
    for spec in ("dock-36A-w17x1-standard-0", "dock-36A-w15x2-storm-0"):
        with pytest.raises(click.UsageError, match=f"not live dock-v1-eval task ids: {spec}"):
            sweep.task_ids(spec, live=True)


def test_a_live_attempt_is_a_row_with_the_weeks_grade_watches_and_planning_calls(fake):
    (fake / "script.json").write_text(json.dumps({
        A: scored(A, SONNET, week(A, reward=1.0, cost=10, excused=0) | {"watches": 5}, summary(SONNET, cost=0.4)),
        B: scored(B, SONNET, week(B, reward=0.8116, end_reason="end_week", cost=246),
                  summary(SONNET, end_reason="turn_limit", reward=None, cost=1.25)),
    }))
    result = sweep_run("--models", SONNET, "--tasks", f"{A},{B}", "--cap-usd", "20", "--parallel", "1")
    assert result.exit_code == 0, result.output
    first, second = sweep.results(Path("results/runs/live"))
    assert list(first) == ROW_KEYS
    assert {key: first[key] for key in ROW_KEYS[14:]} == {
        "reward": 1.0, "submitted": True, "feasible": True, "plan_cost": 10, "optimal_cost": 226, "checks": 14,
        "calls": 31, "end_reason": "done", "turns": 30, "tool_calls": 31, "input_tokens": 412000,
        "output_tokens": 38000, "cached_tokens": 351000, "cache_write_tokens": 40000, "cost_usd": 0.4,
        "agent_reward": 1.0, "transcript": f"transcripts/anthropic-claude-sonnet-5-5/{A}-r1-a1.json", "watches": 5,
        "excused_cost": 0, "regret": -216}
    assert (second["reward"], second["submitted"], second["end_reason"], second["agent_reward"],
            second["excused_cost"], second["regret"]) == (0.8116, False, "turn_limit", None, 20, 20)
    out = Path("results/runs/live")
    assert json.loads((out / "sweep.json").read_text()) == {
        "name": "live", "models": [SONNET], "tasks": [A, B], "k": 1, "episode_cap_usd": 5.0, "live": True}
    assert sorted(p.relative_to(out / "bundle").as_posix() for p in (out / "bundle").rglob("*") if p.is_file()) == [
        "README.md", "artifacts/portsim-live-verifier/verify.py", f"tasks/{B}.json", f"tasks/{A}.json"]
    assert json.loads((out / f"bundle/tasks/{A}.json").read_text()) == tasks.live_steps(
        next(t for t in tasks.pack_tasks("dock-v1-eval") if t.task_id == A), 5.0)
    calls = [json.loads(line) for line in (fake / "calls.jsonl").read_text().splitlines()]
    assert calls[0] == ["run", str((out / "bundle").absolute()), "--task", A, "--dry-run"]
    assert result.output.splitlines()[1] == f"done {SONNET} {A} r1 a1: reward 1.0 (done), $0.4000 (spent $0.40)"


def test_a_week_the_live_verifier_refuses_is_unscored_and_retried(fake):
    (fake / "script.json").write_text(json.dumps({A: unscorable(A, GPT, summary(GPT, cost=0.3))}))
    result = sweep_run("--models", GPT, "--tasks", A, "--cap-usd", "20")
    assert result.exit_code == 0, result.output
    rows = sweep.results(Path("results/runs/live"))
    assert [(r["outcome"], r["failed_step"], r["error_code"], r["retryable"]) for r in rows] == [
        ("failed", "grade", "RuntimeError", True), ("failed", "grade", "RuntimeError", True),
        ("failed", "grade", "RuntimeError", False)]
    assert {key: rows[0][key] for key in ("reward", "submitted", "checks", "calls", "watches", "excused_cost",
                                          "regret", "cost_usd")} == {
        "reward": None, "submitted": None, "checks": None, "calls": None, "watches": None, "excused_cost": None,
        "regret": None, "cost_usd": 0.3}
    assert rows[0]["error"].startswith("the week can't be scored: done True, audit {'ok': False")


def test_an_older_sweep_json_reads_as_v1_and_a_live_run_of_it_is_another_sweep(fake):
    out = Path("results/runs/old")
    out.mkdir(parents=True)
    (out / "sweep.json").write_text(json.dumps({"name": "old", "models": [SONNET], "tasks": [A], "k": 1,
                                                "episode_cap_usd": 5.0}, indent=2) + "\n")
    assert sweep.load("old") == sweep.Sweep("old", [SONNET], [A], 1, 5.0, False)
    sweep.prepare(sweep.load("old"))
    refused = sweep_run("--models", SONNET, "--tasks", A, "--cap-usd", "5", name="old")
    assert refused.exit_code == 2 and "is another sweep" in refused.output
    assert not (fake / "calls.jsonl").exists()
    assert sweep_run("--models", SONNET, "--tasks", "dock-36A-w15x2-storm-0", "--cap-usd", "5").exit_code == 2


def row(name: str, model: str, task: str, rep: int, attempt: int = 1, *, reward: float | None = None,
        cost: float | None = 0.5, code: str | None = None, end_reason: str = "done", agent_reward="reward",
        submitted: bool = True, plan_cost: int | None = None, optimal_cost: int = 10, excused: int = 0,
        turns: int = 22, tokens: tuple[int, int, int] = (300000, 20000, 250000), watches: int = 5) -> dict:
    """A live results.jsonl row as the sweep writes one: scored when it has a reward, else failed with ``code``."""
    scored = reward is not None
    feasible = scored and plan_cost is not None
    return {"sweep": name, "model": model, "task_id": task, "rep": rep, "attempt": attempt,
            "started_utc": "2026-10-07T12:00:00Z", "wall_seconds": 600.0, "exit": 0 if scored else 1,
            "instance": None, "outcome": "scored" if scored else "failed", "failed_step": None if scored else "grade",
            "error_code": code, "error": None, "retryable": False, "reward": reward,
            "submitted": submitted if scored else None, "feasible": feasible if scored else None,
            "plan_cost": plan_cost, "optimal_cost": optimal_cost if scored else None,
            "checks": 12 if scored else None, "calls": 30 if scored else None, "end_reason": end_reason,
            "turns": turns, "tool_calls": 30, "input_tokens": tokens[0], "output_tokens": tokens[1],
            "cached_tokens": tokens[2], "cache_write_tokens": 20000, "cost_usd": cost,
            "agent_reward": reward if agent_reward == "reward" else agent_reward, "transcript": None,
            "watches": watches if scored else None, "excused_cost": excused if scored else None,
            "regret": plan_cost - optimal_cost if feasible else None}


def write(s: sweep.Sweep, rows: list[dict]) -> None:
    s.out.mkdir(parents=True)
    (s.out / "sweep.json").write_text(json.dumps(sweep.asdict(s)))
    (s.out / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


@pytest.fixture
def pilot(tmp_path, monkeypatch) -> list[sweep.Sweep]:
    """Two live sweeps: a refused week retried, an agent reward that differs, an agent that stopped early, an
    infeasible week, a capped episode, and a week played in both sweeps."""
    monkeypatch.chdir(tmp_path)
    first = sweep.Sweep("live-pilot", [SONNET, GPT], [A, B], 1, 6.0, True)
    write(first, [
        row("live-pilot", SONNET, A, 1, reward=1.0, cost=0.9, plan_cost=10),
        row("live-pilot", SONNET, B, 1, code="RuntimeError", cost=1.2),
        row("live-pilot", SONNET, B, 1, 2, reward=0.8116, cost=1.6, plan_cost=246, optimal_cost=226, excused=20,
            agent_reward=0.75, turns=35, tokens=(600000, 40000, 520000), watches=7),
        row("live-pilot", GPT, A, 1, reward=0.1, cost=0.2, end_reason="turn_limit", agent_reward=None,
            submitted=False, turns=27, tokens=(200000, 30000, 0)),
        row("live-pilot", GPT, B, 1, code="cost_cap", cost=2.0, end_reason="cost_cap", agent_reward=None),
    ])
    second = sweep.Sweep("live-more", [SONNET], [A], 1, 6.0, True)
    write(second, [row("live-more", SONNET, A, 1, reward=0.9, cost=None, plan_cost=40, excused=5, turns=24)])
    return [first, second]


EXPECTED = """\
# PortSim live: portsim-llm on the live weeks

Sweeps: `live-pilot` (anthropic/claude-sonnet-5-5, openai/gpt-6.1-sol; 2 tasks, k=1, episode cap $6); `live-more` \
(anthropic/claude-sonnet-5-5; 1 tasks, k=1, episode cap $6).
Harness: portsim-llm. References: the rolling CP-SAT re-planner and the naive online policy, played on the same weeks \
(data/live/references.jsonl).

Spend: $5.90 known; 1 attempts with no spend recorded, $6.00 at the cap. Attempts: 6, retries: 1. Unscored runs: 1 of \
5.

## Per model

| Model | Tasks | Runs scored/planned | Mean reward (95% CI) | Rolling reference | Naive reference \
| Reached done per rep | Feasible | Optimal | Mean regret | Mean excused cost | Median turns \
| Tokens in/out per episode | Cached tokens per episode | Cost per episode | Spend |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| anthropic/claude-sonnet-5-5 | 2 | 3/3 | 0.881 (0.812 to 0.950) | 1.000 | 0.204 | 2 | 2 | 0.5 | 16.667 | 8.333 \
| 24 | 400.0k/26.7k | 340.0k | $1.2500 | $3.70 + 1 unknown |
| openai/gpt-6.1-sol | 1 | 1/2 | 0.100 (0.100 to 0.100) | 1.000 | 0.207 | 0 | 0 | 0 | – | 0.000 | 27 \
| 200.0k/30.0k | 0.0k | $0.2000 | $2.20 |

## Week by week

### anthropic/claude-sonnet-5-5

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | r2 | Mean |
|---|---|---:|---:|---|---|---:|---:|---:|
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | 693 (0.202) | 0.812 | – | 0.812 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | 274 (0.207) | 1.000 | 0.900 | 0.950 |

### openai/gpt-6.1-sol

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | 693 (0.202) | – | – |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | 274 (0.207) | 0.100 | 0.100 |

## Unscored runs

| Sweep | Model | Task | Rep | Attempts | Last outcome | Spend |
|---|---|---|---:|---:|---|---:|
| live-pilot | openai/gpt-6.1-sol | dock-24B-w07x1-busy-0 | 1 | 1 | cost_cap | $2.00 |

## Runs whose agent reward differs from the verifier's

Only runs whose agent saw the week end.

| Sweep | Model | Task | Rep | Agent reward | Verifier reward |
|---|---|---|---:|---:|---:|
| live-pilot | anthropic/claude-sonnet-5-5 | dock-24B-w07x1-busy-0 | 1 | 0.750 | 0.812 |
"""


def test_the_live_report_of_a_fixed_set_of_results(pilot):
    assert sweep.live_report(pilot) == EXPECTED


def test_report_live_writes_results_live_md_and_never_mixes_live_and_v1_sweeps(pilot):
    result = CliRunner().invoke(portsim, ["sweep", "report", "--live", "live-pilot", "live-more"])
    assert result.exit_code == 0, result.output
    assert result.output == "Wrote results/live.md\n"
    assert Path("results/live.md").read_text() == EXPECTED
    assert CliRunner().invoke(portsim, ["sweep", "report", "--live", "live-pilot", "live-more", "--out",
                                        "l.md"]).exit_code == 0
    assert Path("l.md").read_text() == EXPECTED
    write(sweep.Sweep("v1", [SONNET], [A], 1, 5.0), [])
    mixed = CliRunner().invoke(portsim, ["sweep", "report", "--live", "live-pilot", "v1"])
    assert mixed.exit_code == 2 and "not live sweeps: v1; report them without --live" in mixed.output
    mixed = CliRunner().invoke(portsim, ["sweep", "report", "v1", "live-more", "live-pilot"])
    assert mixed.exit_code == 2 and "live sweeps: live-more, live-pilot; report them with --live" in mixed.output
    assert not Path("results/parity.md").exists()
