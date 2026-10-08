"""`agent-env portsim sweep run|report --wind`, on the synthetic wind pack: the wind weeks and their order, the wind
flag in sweep.json while older sweep.json files still load, wind rows from a stand-in `agent-env run` playing the wind
bundle, and the wind report against the hindsight optimum, the anchor and the wind references, never mixed with other
sweeps."""

import json
import sys
import textwrap
from pathlib import Path

import click
import pytest
from berth_core import TaskPack
from click.testing import CliRunner
from live_contexts import scored, summary, week
from wind_fixtures import BUST_TASK, OTHER_TASK, PACK_DIR, STORM_TASK, use

from agentenv_portsim import sweep, tasks, wind
from agentenv_portsim.cli import portsim

SONNET, GPT = "anthropic/claude-sonnet-5-5", "openai/gpt-6.1-sol"
V3 = "dock-24B-w07x1-busy-0"
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


@pytest.fixture(autouse=True)
def fixtures(monkeypatch):
    use(monkeypatch)


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


def sweep_run(*args: str, name: str = "wind"):
    return CliRunner().invoke(portsim, ["sweep", "run", "--wind", "--name", name, *args])


def test_the_wind_weeks_run_by_watches_and_a_listed_week_must_be_a_wind_week():
    ids = sweep.task_ids("all", wind=True)
    assert ids == [BUST_TASK, STORM_TASK] and sorted(ids) == sorted(wind.task_ids())
    assert sweep.task_ids("all", live=True, wind=True) == ids
    assert sweep.task_ids(f"{STORM_TASK},{BUST_TASK}", wind=True) == [STORM_TASK, BUST_TASK]
    for spec in (OTHER_TASK, V3):
        with pytest.raises(click.UsageError, match=f"not wind dock-v1-eval task ids: {spec}"):
            sweep.task_ids(spec, wind=True)


def test_a_wind_sweep_plays_the_wind_bundle_and_records_live_rows(fake):
    (fake / "script.json").write_text(json.dumps({STORM_TASK: scored(STORM_TASK, SONNET, week(
        STORM_TASK, reward=0.95, cost=240, excused=96, watches=8, grade={
            "reward": 0.95, "feasible": True, "clean_fraction": 1.0, "quality": 0.95, "cost": 240, "raw_cost": 336,
            "excused_cost": 96, "optimal_cost": 234, "unavoidable_cost": 177, "regret": 6, "violations": [],
            "excused": []}), summary(SONNET, reward=0.95, cost=0.5))}))
    result = sweep_run("--models", SONNET, "--tasks", STORM_TASK, "--cap-usd", "20")
    assert result.exit_code == 0, result.output
    out = Path("results/runs/wind")
    [row] = sweep.results(out)
    assert {key: row[key] for key in ("reward", "submitted", "feasible", "plan_cost", "optimal_cost", "checks",
                                      "watches", "excused_cost", "regret", "cost_usd")} == {
        "reward": 0.95, "submitted": True, "feasible": True, "plan_cost": 240, "optimal_cost": 234, "checks": 14,
        "watches": 8, "excused_cost": 96, "regret": 6, "cost_usd": 0.5}
    assert json.loads((out / "sweep.json").read_text()) == {
        "name": "wind", "models": [SONNET], "tasks": [STORM_TASK], "k": 1, "episode_cap_usd": 5.0, "live": True,
        "wind": True}
    assert sweep.load("wind") == sweep.Sweep("wind", [SONNET], [STORM_TASK], 1, 5.0, True, wind=True)
    assert (out / "bundle/README.md").read_text().startswith("PortSim wind dock-v1-eval: 1 weeks, each played in "
                                                             "watches by the portsim-llm agent on portsim-wind")
    assert json.loads((out / f"bundle/tasks/{STORM_TASK}.json").read_text()) == tasks.live_steps(
        wind.pack().get(STORM_TASK), 5.0, env="portsim-wind", week=wind.WindWeek, rules=tasks.WIND_RULES)
    calls = [json.loads(line) for line in (fake / "calls.jsonl").read_text().splitlines()]
    assert calls == [["run", str((out / "bundle").absolute()), "--task", STORM_TASK, "--dry-run"],
                     ["run", str((out / "bundle").absolute()), "--task", STORM_TASK, "--model", SONNET]]


def test_older_sweeps_read_as_not_wind_and_a_wind_run_of_one_is_another_sweep(fake):
    marine = sweep.Sweep("old", [SONNET], [V3], 1, 5.0, True, True)
    sweep.prepare(marine)
    assert "wind" not in json.loads((marine.out / "sweep.json").read_text())
    assert sweep.load("old") == marine and not marine.wind
    v3_json = {"name": "v3", "models": [SONNET], "tasks": [V3], "k": 1, "episode_cap_usd": 5.0, "live": True,
               "marine": True}
    (sweep.RUNS / "v3").mkdir()
    (sweep.RUNS / "v3/sweep.json").write_text(json.dumps(v3_json, indent=2) + "\n")
    assert sweep.load("v3") == sweep.Sweep("v3", [SONNET], [V3], 1, 5.0, True, True, None, False)
    refused = sweep_run("--models", SONNET, "--tasks", STORM_TASK, "--cap-usd", "5", name="old")
    assert refused.exit_code == 2 and "is another sweep" in refused.output
    both = sweep_run("--marine", "--models", SONNET, "--tasks", STORM_TASK, "--cap-usd", "5", name="both")
    assert both.exit_code == 2 and "--wind and --marine play different envs: pick one" in both.output
    assert sweep_run("--models", SONNET, "--tasks", OTHER_TASK, "--cap-usd", "5").exit_code == 2
    assert not (fake / "calls.jsonl").exists() and not Path("results/runs/both").exists()


def row(name: str, model: str, task: str, *, reward: float | None, plan_cost: int | None, optimal_cost: int,
        cost: float = 0.5, excused: int = 0, code: str | None = None) -> dict:
    """A wind results.jsonl row as the sweep writes one: scored when it has a reward, else failed with ``code``."""
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
            "watches": 8 if has_reward else None, "excused_cost": excused if has_reward else None,
            "regret": plan_cost - optimal_cost if feasible else None}


def write(s: sweep.Sweep, rows: list[dict]) -> None:
    s.out.mkdir(parents=True)
    (s.out / "sweep.json").write_text(json.dumps(sweep.asdict(s)))
    (s.out / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


@pytest.fixture
def pilot(tmp_path, monkeypatch) -> list[sweep.Sweep]:
    """A wind sweep of two models over a storm week and a bust week: a cost under hindsight net of the excused wind, an
    infeasible week and an unscored run."""
    monkeypatch.chdir(tmp_path)
    s = sweep.Sweep("wind-pilot", [SONNET, GPT], [BUST_TASK, STORM_TASK], 1, 4.0, True, wind=True)
    write(s, [
        row("wind-pilot", SONNET, BUST_TASK, reward=1.0, plan_cost=226, optimal_cost=226, cost=0.5),
        row("wind-pilot", SONNET, STORM_TASK, reward=0.95, plan_cost=240, optimal_cost=234, cost=0.8, excused=96),
        row("wind-pilot", GPT, BUST_TASK, reward=None, plan_cost=None, optimal_cost=226, cost=0.3, code="RuntimeError"),
        row("wind-pilot", GPT, STORM_TASK, reward=0.188235, plan_cost=None, optimal_cost=234, cost=0.2),
    ])
    return [s]


EXPECTED = """\
# PortSim wind: portsim-llm on the live weeks in real Barcelona wind

Sweeps: `wind-pilot` (anthropic/claude-sonnet-5-5, openai/gpt-6.1-sol; 2 tasks, k=1, episode cap $4).
Harness: portsim-llm. References, on the same weeks (data/wind/references.jsonl): hindsight, the CP-SAT optimum on \
the wind that blew; the anchor that rewards and regret are scored against, the lower of hindsight and the best cost \
of the rolling re-planner following the forecasts; that rolling re-planner; blind, the same without the forecasts; \
hold, in bust weeks, the same holding every warning; and the naive online policy.

Spend: $1.80 known; 0 attempts with no spend recorded, $0.00 at the cap. Attempts: 4, retries: 0. Unscored runs: 1 of \
4.

## Per model

| Model | Tasks | Runs scored/planned | Mean reward (95% CI) | Rolling reference | Blind reference | Naive reference \
| Reached done per rep | Feasible | At the anchor | Mean regret vs anchor | Mean regret vs hindsight | Mean excused \
cost | Median turns | Tokens in/out per episode | Cached tokens per episode | Cost per episode | Spend |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| anthropic/claude-sonnet-5-5 | 2 | 2/2 | 0.975 (0.950 to 1.000) | 1.000 | 0.594 | 0.165 | 2 | 2 | 1 | 3.000 | -2.000 \
| 48.000 | 20 | 300.0k/20.0k | 250.0k | $0.6500 | $1.30 |
| openai/gpt-6.1-sol | 1 | 1/2 | 0.188 (0.188 to 0.188) | 1.000 | 0.188 | 0.165 | 1 | 0 | 0 | – | – | 0.000 | 20 | \
300.0k/20.0k | 250.0k | $0.2000 | $0.50 |

## Week by week

Hindsight, the anchor and the references as cost (reward); hold is played in bust weeks only.

### anthropic/claude-sonnet-5-5

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Rolling | Blind | Hold | Naive | r1 | Mean | Regret \
vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|
| dock-24B-w07x1-busy-0-e00 | 2000-W02 storm | busy | 17 | 8 | 244 (0.904) | 234 (1.000) | 234 (1.000) | infeasible \
(0.188) | – | infeasible (0.165) | 0.950 | 0.950 | -4 | 6 |
| dock-24B-w07x1-busy-0-e01 | 2000-W03 bust | busy | 17 | 7 | 226 (1.000) | 226 (1.000) | 226 (1.000) | 226 (1.000) | \
346 (0.360) | infeasible (0.165) | 1.000 | 1.000 | 0 | 0 |

### openai/gpt-6.1-sol

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Rolling | Blind | Hold | Naive | r1 | Mean | Regret \
vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|
| dock-24B-w07x1-busy-0-e00 | 2000-W02 storm | busy | 17 | 8 | 244 (0.904) | 234 (1.000) | 234 (1.000) | infeasible \
(0.188) | – | infeasible (0.165) | 0.188 | 0.188 | – | – |
| dock-24B-w07x1-busy-0-e01 | 2000-W03 bust | busy | 17 | 7 | 226 (1.000) | 226 (1.000) | 226 (1.000) | 226 (1.000) | \
346 (0.360) | infeasible (0.165) | – | – | – | – |

## Unscored runs

| Sweep | Model | Task | Rep | Attempts | Last outcome | Spend |
|---|---|---|---:|---:|---|---:|
| wind-pilot | openai/gpt-6.1-sol | dock-24B-w07x1-busy-0-e01 | 1 | 1 | RuntimeError | $0.30 |

## Runs whose agent reward differs from the verifier's

Only runs whose agent saw the week end.

None.
"""


def test_the_wind_report_of_a_fixed_set_of_results(pilot):
    assert sweep.wind_report(pilot) == EXPECTED


def test_the_wind_report_reads_the_weeks_from_the_wind_pack(pilot):
    pooled = sweep.Wind(pilot)
    assert pooled.pack == {t.task_id: t for t in TaskPack(PACK_DIR).tasks}
    assert pooled.weather == {STORM_TASK: "2000-W02 storm", BUST_TASK: "2000-W03 bust", OTHER_TASK: "2000-W02 storm"}


def test_report_wind_writes_results_wind_md_and_never_mixes_modes(pilot):
    result = CliRunner().invoke(portsim, ["sweep", "report", "--wind", "wind-pilot"])
    assert result.exit_code == 0, result.output
    assert result.output == "Wrote results/wind.md\n"
    assert Path("results/wind.md").read_text() == EXPECTED
    assert not [p.name for p in Path("results").glob("*.md") if p.name != "wind.md"]
    write(sweep.Sweep("v1", [SONNET], [V3], 1, 5.0), [])
    write(sweep.Sweep("live", [SONNET], [V3], 1, 5.0, True), [])
    write(sweep.Sweep("marine", [SONNET], [V3], 1, 5.0, True, True), [])
    for args, message in [
        (["--wind", "wind-pilot", "marine"], "marine sweeps: marine; report them with --marine"),
        (["--marine", "marine", "wind-pilot"], "wind sweeps: wind-pilot; report them with --wind"),
        (["--live", "wind-pilot", "live"], "wind sweeps: wind-pilot; report them with --wind"),
        (["wind-pilot", "v1"], "wind sweeps: wind-pilot; report them with --wind"),
        (["--wind", "v1", "live"],
         "not wind sweeps: v1; report them without --wind; live sweeps: live; report them with --live"),
        (["--wind", "--marine", "wind-pilot"], "--wind and --marine report different envs: pick one"),
    ]:
        mixed = CliRunner().invoke(portsim, ["sweep", "report", *args])
        assert mixed.exit_code == 2 and message in " ".join(mixed.output.split()), mixed.output
