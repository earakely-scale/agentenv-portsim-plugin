"""`agent-env portsim sweep run|report --marine`: the marine weeks and their order, the marine flag in sweep.json,
marine rows from a stand-in `agent-env run` playing the marine bundle, and the marine report against the marine
references, never mixed with v1 or live sweeps."""

import json
import sys
import textwrap
from pathlib import Path

import click
import pytest
from click.testing import CliRunner
from live_contexts import scored, summary, week

from agentenv_portsim import marine, sweep, tasks
from agentenv_portsim.cli import portsim

SONNET, GPT = "anthropic/claude-sonnet-5-5", "openai/gpt-6.1-sol"
A, B, C = "dock-36A-w35x1-standard-0", "dock-24B-w07x1-busy-0", "dock-24B-w06x1-busy-0"
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


def sweep_run(*args: str, name: str = "marine"):
    return CliRunner().invoke(portsim, ["sweep", "run", "--marine", "--name", name, *args])


def test_the_marine_weeks_run_g2_first_then_by_watches_and_a_listed_week_must_be_a_marine_week():
    ids = sweep.task_ids("all", marine=True)
    assert ids == ["dock-24B-w06x1-busy-0", "dock-36A-w05x1-busy-0", A, "dock-36A-w10x1-standard-0",
                   "dock-36A-w06x1-standard-0", "dock-24B-w06x1-standard-0", "dock-24B-w37x1-standard-0",
                   "dock-36A-w15x1-standard-0", "dock-36A-w17x1-busy-0", "dock-36A-w37x1-standard-0",
                   "dock-36A-w06x1-busy-0", B, "dock-36A-w37x1-busy-0", "dock-24B-w35x1-busy-0",
                   "dock-24B-w16x1-busy-0"]
    assert sorted(ids) == sorted(marine.task_ids())
    assert sweep.task_ids("all", live=True, marine=True) == ids
    assert sweep.task_ids("g2", marine=True) == [A, "dock-24B-w06x1-busy-0", "dock-36A-w05x1-busy-0"]
    assert sweep.task_ids(f"{B},{A}", marine=True) == [B, A]
    for spec in ("dock-36A-w15x1-busy-0", "dock-36A-w15x2-storm-0"):
        with pytest.raises(click.UsageError, match=f"not marine dock-v1-eval task ids: {spec}"):
            sweep.task_ids(spec, marine=True)


def test_a_marine_sweep_plays_the_marine_bundle_and_records_live_rows(fake):
    (fake / "script.json").write_text(json.dumps({
        B: scored(B, SONNET, week(B, reward=0.9, cost=240, excused=12), summary(SONNET, reward=0.9, cost=0.5))}))
    result = sweep_run("--models", SONNET, "--tasks", B, "--cap-usd", "20")
    assert result.exit_code == 0, result.output
    out = Path("results/runs/marine")
    [row] = sweep.results(out)
    assert {key: row[key] for key in ("reward", "submitted", "feasible", "plan_cost", "optimal_cost", "checks",
                                      "watches", "excused_cost", "regret", "cost_usd")} == {
        "reward": 0.9, "submitted": True, "feasible": True, "plan_cost": 240, "optimal_cost": 226, "checks": 14,
        "watches": 7, "excused_cost": 12, "regret": 14, "cost_usd": 0.5}
    assert json.loads((out / "sweep.json").read_text()) == {
        "name": "marine", "models": [SONNET], "tasks": [B], "k": 1, "episode_cap_usd": 5.0, "live": True,
        "marine": True}
    assert sweep.load("marine") == sweep.Sweep("marine", [SONNET], [B], 1, 5.0, True, True)
    assert (out / "bundle/README.md").read_text().startswith("PortSim marine dock-v1-eval: 1 weeks, each played in "
                                                             "watches by the portsim-llm agent on portsim-marine")
    assert json.loads((out / f"bundle/tasks/{B}.json").read_text()) == tasks.live_steps(
        marine.pack().get(B), 5.0, env="portsim-marine", week=marine.MarineWeek)
    calls = [json.loads(line) for line in (fake / "calls.jsonl").read_text().splitlines()]
    assert calls == [["run", str((out / "bundle").absolute()), "--task", B, "--dry-run"],
                     ["run", str((out / "bundle").absolute()), "--task", B, "--model", SONNET]]


def test_a_live_sweep_reads_as_not_marine_and_a_marine_run_of_it_is_another_sweep(fake):
    live = sweep.Sweep("old", [SONNET], [A], 1, 5.0, True)
    sweep.prepare(live)
    assert json.loads((live.out / "sweep.json").read_text())["live"] is True
    assert "marine" not in json.loads((live.out / "sweep.json").read_text())
    assert sweep.load("old") == live and not live.marine
    refused = sweep_run("--models", SONNET, "--tasks", A, "--cap-usd", "5", name="old")
    assert refused.exit_code == 2 and "is another sweep" in refused.output
    assert sweep_run("--models", SONNET, "--tasks", "dock-36A-w15x1-busy-0", "--cap-usd", "5").exit_code == 2
    assert not (fake / "calls.jsonl").exists()


def row(name: str, model: str, task: str, *, reward: float | None, plan_cost: int | None, optimal_cost: int,
        cost: float = 0.5, excused: int = 0, code: str | None = None) -> dict:
    """A marine results.jsonl row as the sweep writes one: scored when it has a reward, else failed with ``code``."""
    has_reward = reward is not None
    feasible = has_reward and plan_cost is not None
    return {"sweep": name, "model": model, "task_id": task, "rep": 1, "attempt": 1,
            "started_utc": "2026-10-07T12:00:00Z", "wall_seconds": 600.0, "exit": 0 if has_reward else 1,
            "instance": None, "outcome": "scored" if has_reward else "failed",
            "failed_step": None if has_reward else "grade",
            "error_code": code, "error": None, "retryable": False, "reward": reward,
            "submitted": True if has_reward else None, "feasible": feasible if has_reward else None,
            "plan_cost": plan_cost, "optimal_cost": optimal_cost if has_reward else None,
            "checks": 12 if has_reward else None, "calls": 30 if has_reward else None, "end_reason": "done",
            "turns": 20, "tool_calls": 30, "input_tokens": 300000, "output_tokens": 20000, "cached_tokens": 250000,
            "cache_write_tokens": 20000, "cost_usd": cost, "agent_reward": reward, "transcript": None,
            "watches": 5 if has_reward else None, "excused_cost": excused if has_reward else None,
            "regret": plan_cost - optimal_cost if feasible else None}


def write(s: sweep.Sweep, rows: list[dict]) -> None:
    s.out.mkdir(parents=True)
    (s.out / "sweep.json").write_text(json.dumps(sweep.asdict(s)))
    (s.out / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


@pytest.fixture
def pilot(tmp_path, monkeypatch) -> list[sweep.Sweep]:
    """A marine sweep of two models over three weeks: a week short of tugs, an excused cost and an unscored run."""
    monkeypatch.chdir(tmp_path)
    s = sweep.Sweep("marine-pilot", [SONNET, GPT], [A, B, C], 1, 4.0, True, True)
    write(s, [
        row("marine-pilot", SONNET, A, reward=1.0, plan_cost=10, optimal_cost=10, cost=0.8),
        row("marine-pilot", SONNET, B, reward=0.164706, plan_cost=None, optimal_cost=226, cost=1.1),
        row("marine-pilot", SONNET, C, reward=0.95, plan_cost=95, optimal_cost=87, cost=0.7, excused=6),
        row("marine-pilot", GPT, A, reward=0.9, plan_cost=12, optimal_cost=10, cost=0.2),
        row("marine-pilot", GPT, B, reward=None, plan_cost=None, optimal_cost=226, cost=0.3, code="RuntimeError"),
        row("marine-pilot", GPT, C, reward=1.0, plan_cost=87, optimal_cost=87, cost=0.1),
    ])
    return [s]


EXPECTED = """\
# PortSim marine: portsim-llm on the live weeks with pilots and tugs

Sweeps: `marine-pilot` (anthropic/claude-sonnet-5-5, openai/gpt-6.1-sol; 3 tasks, k=1, episode cap $4).
Harness: portsim-llm. References: the rolling CP-SAT re-planner and the naive online policy, played on the same weeks \
with pilots and tugs (data/marine/references.jsonl).

Spend: $3.20 known; 0 attempts with no spend recorded, $0.00 at the cap. Attempts: 6, retries: 0. Unscored runs: 1 of \
6.

## Per model

| Model | Tasks | Runs scored/planned | Mean reward (95% CI) | Rolling reference | Naive reference \
| Reached done per rep | Feasible | Optimal | Mean regret | Mean excused cost | Median turns \
| Tokens in/out per episode | Cached tokens per episode | Cost per episode | Spend |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| anthropic/claude-sonnet-5-5 | 3 | 3/3 | 0.705 (0.165 to 1.000) | 1.000 | 0.181 | 3 | 2 | 1 | 4.000 | 2.000 | 20 \
| 300.0k/20.0k | 250.0k | $0.8667 | $2.60 |
| openai/gpt-6.1-sol | 2 | 2/3 | 0.950 (0.900 to 1.000) | 1.000 | 0.190 | 2 | 2 | 1 | 1.000 | 0.000 | 20 \
| 300.0k/20.0k | 250.0k | $0.1500 | $0.60 |

## Week by week

### anthropic/claude-sonnet-5-5

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.950 | 0.950 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | 0.165 | 0.165 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 1.000 | 1.000 |

### openai/gpt-6.1-sol

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 1.000 | 1.000 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | – | – |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 0.900 | 0.900 |

## Unscored runs

| Sweep | Model | Task | Rep | Attempts | Last outcome | Spend |
|---|---|---|---:|---:|---|---:|
| marine-pilot | openai/gpt-6.1-sol | dock-24B-w07x1-busy-0 | 1 | 1 | RuntimeError | $0.30 |

## Runs whose agent reward differs from the verifier's

Only runs whose agent saw the week end.

None.
"""


def test_the_marine_report_of_a_fixed_set_of_results(pilot):
    assert sweep.live_report(pilot) == EXPECTED


def test_report_marine_writes_results_marine_md_and_never_mixes_modes(pilot):
    result = CliRunner().invoke(portsim, ["sweep", "report", "--marine", "marine-pilot"])
    assert result.exit_code == 0, result.output
    assert result.output == "Wrote results/marine.md\n"
    assert Path("results/marine.md").read_text() == EXPECTED
    assert not Path("results/live.md").exists() and not Path("results/parity.md").exists()
    write(sweep.Sweep("v1", [SONNET], [A], 1, 5.0), [])
    write(sweep.Sweep("live", [SONNET], [A], 1, 5.0, True), [])
    for args, message in [
        (["--marine", "marine-pilot", "live"], "live sweeps: live; report them with --live"),
        (["--marine", "v1", "marine-pilot"], "not marine sweeps: v1; report them without --marine"),
        (["--live", "marine-pilot", "live"], "marine sweeps: marine-pilot; report them with --marine"),
        (["marine-pilot", "v1"], "marine sweeps: marine-pilot; report them with --marine"),
        (["--marine", "live", "v1"],
         "live sweeps: live; report them with --live; not marine sweeps: v1; report them without --marine"),
    ]:
        mixed = CliRunner().invoke(portsim, ["sweep", "report", *args])
        assert mixed.exit_code == 2 and message in " ".join(mixed.output.split()), mixed.output
