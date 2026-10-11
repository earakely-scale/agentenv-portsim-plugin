"""`agent-env portsim sweep report`: the published run it compares against, its numbers when the runs equal the
published episodes, the whole Markdown for a fixed set of results, and the G2 weeks."""

import hashlib
import json
import statistics
from math import floor
from pathlib import Path

import pytest
from click.testing import CliRunner

from agentenv_portsim import lines, sweep, tasks, wind
from agentenv_portsim.cli import portsim

SONNET, GPT, GLM, HAIKU = ("anthropic/claude-sonnet-5-5", "openai/gpt-6.1-sol", "fireworks_ai/glm-5p3-flash",
                           "anthropic/claude-haiku-4-5")
A, B = "dock-24B-w06x1-busy-0", "dock-36A-w15x2-storm-0"
UPSTREAM = Path(__file__).resolve().parents[2] / "data/published/dock-eval50/index.json"


def published() -> dict[tuple[str, str], dict]:
    return {(e["model"], e["task_id"]): e for e in json.loads(sweep.PUBLISHED_INDEX.read_text())["episodes"]}


def row(name: str, model: str, task: str, rep: int, attempt: int = 1, *, reward: float | None = None,
        cost: float | None = 0.1, code: str | None = None, outcome: str | None = None, agent_reward="reward",
        feasible: bool = True, plan_cost: int | None = 100, optimal_cost: int = 100, turns: int = 2,
        tokens: tuple[int, int] = (20000, 5000), submitted: bool = True) -> dict:
    """A results.jsonl row as the sweep writes one: scored when it has a reward, else failed with ``code``."""
    scored = reward is not None
    return {"sweep": name, "model": model, "task_id": task, "rep": rep, "attempt": attempt,
            "started_utc": "2026-10-06T12:00:00Z", "wall_seconds": 60.0, "exit": 0 if scored else 1,
            "instance": None, "outcome": outcome or ("scored" if scored else "failed"),
            "failed_step": None if scored else "play", "error_code": code, "error": None, "retryable": False,
            "reward": reward, "submitted": submitted if scored else None, "feasible": feasible if scored else None,
            "plan_cost": plan_cost if scored else None, "optimal_cost": optimal_cost if scored else None,
            "checks": 1, "calls": 2, "end_reason": "submitted" if submitted else "no_tool_call", "turns": turns,
            "tool_calls": 2, "input_tokens": tokens[0], "output_tokens": tokens[1], "cached_tokens": 0,
            "cache_write_tokens": 0, "cost_usd": cost, "agent_reward": reward if agent_reward == "reward" else
            agent_reward, "transcript": None}


def write(s: sweep.Sweep, rows: list[dict]) -> None:
    s.out.mkdir(parents=True)
    (s.out / "sweep.json").write_text(json.dumps(sweep.asdict(s)))
    (s.out / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_the_published_run_is_upstreams_index_byte_for_byte():
    assert sweep.PUBLISHED_INDEX.read_bytes() == UPSTREAM.read_bytes()
    assert hashlib.sha256(UPSTREAM.read_bytes()).hexdigest() == (
        "827601faba281f0587d562e49b5c7c189943b8240246dc2190fe3c047d3c4087")
    index = json.loads(UPSTREAM.read_text())
    assert (index["run"], len(index["episodes"])) == ("dock-eval50", 300)
    assert {e["model"] for e in index["episodes"]} == set(sweep.PUBLISHED.values())


UPSTREAM_README = {
    SONNET: ("0.782 (0.711 to 0.849)", "0.921 / 0.921 | 0.797 / 0.797 | 0.675 / 0.675 | 0.774 / 0.774", 49, 49, 10),
    GPT: ("0.888 (0.833 to 0.940)", "0.998 / 0.998 | 0.900 / 0.900 | 0.864 / 0.864 | 0.822 / 0.822", 50, 50, 26),
    GLM: ("0.470 (0.357 to 0.588)", "0.767 / 0.767 | 0.500 / 0.500 | 0.460 / 0.460 | 0.240 / 0.240", 36, 25, 9),
    "fireworks_ai/qwen3p8-2p4t-a95b": (
        "0.380 (0.271 to 0.493)", "0.580 / 0.580 | 0.449 / 0.449 | 0.328 / 0.328 | 0.215 / 0.215", 34, 23, 5),
    "fireworks_ai/glm-5p3": (
        "0.313 (0.198 to 0.440)", "0.624 / 0.624 | 0.342 / 0.342 | 0.224 / 0.224 | 0.154 / 0.154", 17, 16, 10),
    "groq/qwen/qwen3.8-27b": (
        "0.211 (0.115 to 0.318)", "0.397 / 0.397 | 0.274 / 0.274 | 0.219 / 0.219 | 0.003 / 0.003", 16, 13, 3),
}


def test_runs_that_equal_the_published_episodes_report_upstreams_numbers(tmp_path, monkeypatch):
    """Each model's mean and CI, tier means, and submitted, feasible and optimal counts, as upstream's README has
    them."""
    monkeypatch.chdir(tmp_path)
    episodes, ids = published(), sweep.task_ids("all")
    s = sweep.Sweep("same", list(UPSTREAM_README), ids, 2, 5.0)
    write(s, [row("same", m, t, rep, reward=e["reward"], feasible=e["feasible"], plan_cost=e["cost"],
                  optimal_cost=e["optimal_cost"], turns=e["turns"], submitted=e["submitted"],
                  tokens=(e["input_tokens"], e["output_tokens"]), agent_reward=e["reward"] if e["submitted"] else None)
              for m in UPSTREAM_README for rep in (1, 2) for t in ids for e in [episodes[sweep.PUBLISHED[m], t]]])
    text = sweep.report([s])
    for model, (mean, tier, submitted, feasible, optimal) in UPSTREAM_README.items():
        [line] = [line for line in text.splitlines() if line.startswith(f"| {model} | {sweep.PUBLISHED[model]} |")]
        cells = line.split(" | ")
        assert cells[3:10] == ["100/100", mean, mean, "+0.000 (+0.000 to +0.000)", f"{submitted} / {submitted}",
                               f"{feasible} / {feasible}", f"{optimal} / {optimal}"]
        assert f"| {model} | {tier} |" in text
    assert "Unscored runs: 0 of 600." in text
    assert text.endswith("## Unscored runs\n\nNone.\n\n## Runs whose agent reward differs from the verifier's\n\n"
                         "None.\n")


@pytest.fixture
def pilot(tmp_path, monkeypatch) -> list[sweep.Sweep]:
    """Two sweeps: retries, a capped episode, an interrupted attempt, runs with no instance, a run never played, a
    no-submit, an agent reward that differs, and a model upstream didn't publish."""
    monkeypatch.chdir(tmp_path)
    first = sweep.Sweep("pilot", [SONNET, GPT], [A, B], 2, 0.5)
    write(first, [
        row("pilot", SONNET, A, 1, reward=0.9, cost=0.2, plan_cost=95, optimal_cost=87, tokens=(25000, 17000)),
        row("pilot", SONNET, A, 2, code="provider_error", cost=0.05),
        row("pilot", SONNET, A, 2, 2, reward=0.95, cost=0.25, plan_cost=87, optimal_cost=87, turns=3),
        row("pilot", SONNET, B, 1, reward=0.0, cost=0.1, feasible=False, plan_cost=None, optimal_cost=369,
            submitted=False, agent_reward=None),
        row("pilot", SONNET, B, 2, reward=0.5, cost=0.3, plan_cost=369, optimal_cost=369, turns=6,
            tokens=(500000, 80000), agent_reward=0.45),
        row("pilot", GPT, A, 1, reward=1.0, plan_cost=87, optimal_cost=87, tokens=(7000, 4000)),
        row("pilot", GPT, A, 2, outcome="interrupted", cost=None),
        row("pilot", GPT, A, 2, 2, code="cost_cap", cost=0.49),
        *(row("pilot", GPT, B, 1, n, code="no_instance", cost=None) for n in (1, 2, 3)),
    ])
    second = sweep.Sweep("extra", [GLM, HAIKU], [A], 1, 0.75)
    write(second, [row("extra", GLM, A, 1, reward=0.6, cost=0.01), row("extra", HAIKU, A, 1, reward=0.3, cost=0.02)])
    return [first, second]


EXPECTED = """\
# PortSim parity: portsim-llm against the published dock-eval50 run

Sweeps: `pilot` (anthropic/claude-sonnet-5-5, openai/gpt-6.1-sol; 2 tasks, k=2, episode cap $0.5); `extra` \
(fireworks_ai/glm-5p3-flash, anthropic/claude-haiku-4-5; 1 tasks, k=1, episode cap $0.75).
Harness: portsim-llm. Published: dock-eval50 @ b0f4c2f, 300 episodes.

Spend: $1.52 known; 4 attempts with no spend recorded, $2.00 at the cap. Attempts: 13, retries: 4. Unscored runs: 3 \
of 10.

## Per model

| Model | Published as | Tasks | Runs scored/planned | Ours mean (95% CI) | Published mean on these tasks (95% CI) \
| Mean diff ours−published (95% CI) | Submitted per rep / published | Feasible | Optimal | Median turns ours/published \
| Tokens in/out per episode ours/published | Cost per episode | Spend |
|---|---|---:|---:|---|---|---|---:|---:|---:|---:|---|---:|---:|
| anthropic/claude-sonnet-5-5 | anthropic:claude-sonnet-5-5 | 2 | 4/4 | 0.588 (0.250 to 0.925) \
| 0.662 (0.379 to 0.944) | -0.074 (-0.129 to -0.019) | 1.5 / 2 | 1.5 / 2 | 1 / 0 | 2.5 / 5 \
| 141.2k/26.8k vs 304.2k/52.7k | $0.2125 | $0.90 |
| openai/gpt-6.1-sol | openai:gpt-6.1-sol | 1 | 1/4 | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) \
| +0.000 (+0.000 to +0.000) | 1 / 1 | 1 / 1 | 1 / 1 | 2 / 2 | 7.0k/4.0k vs 7.3k/4.2k | $0.1000 | $0.59 + 4 unknown |
| fireworks_ai/glm-5p3-flash | hf:zai-org/GLM-5.3-Flash:baseten | 1 | 1/1 | 0.600 (0.600 to 0.600) \
| 0.864 (0.864 to 0.864) | -0.264 (-0.264 to -0.264) | 1 / 1 | 1 / 1 | 1 / 0 | 2 / 3 | 20.0k/5.0k vs 14.1k/32.5k \
| $0.0100 | $0.01 |
| anthropic/claude-haiku-4-5 | – | 1 | 1/1 | 0.300 (0.300 to 0.300) | – | – | 1 / – | 1 / – | 1 / – | 2 / – \
| 20.0k/5.0k vs – | $0.0200 | $0.02 |

## Per tier

Mean reward over each tier's tasks, ours / published.

| Model | standard | busy | storm | extreme |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5-5 | – | 0.925 / 0.944 | 0.250 / 0.379 | – |
| openai/gpt-6.1-sol | – | 1.000 / 1.000 | – | – |
| fireworks_ai/glm-5p3-flash | – | 0.600 / 0.864 | – | – |
| anthropic/claude-haiku-4-5 | – | 0.300 / – | – | – |

## Week by week

### anthropic/claude-sonnet-5-5

| Task | Tier | Ships | Published (reward, end, turns) | r1 | r2 | Ours mean | Diff |
|---|---|---:|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 0.944 (submitted, 2) | 0.900 | 0.950 | 0.925 | -0.019 |
| dock-36A-w15x2-storm-0 | storm | 56 | 0.379 (submitted, 8) | 0.000 | 0.500 | 0.250 | -0.129 |

### openai/gpt-6.1-sol

| Task | Tier | Ships | Published (reward, end, turns) | r1 | r2 | Ours mean | Diff |
|---|---|---:|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 1.000 (submitted, 2) | 1.000 | – | 1.000 | +0.000 |
| dock-36A-w15x2-storm-0 | storm | 56 | 0.591 (submitted, 6) | – | – | – | – |

### fireworks_ai/glm-5p3-flash

| Task | Tier | Ships | Published (reward, end, turns) | r1 | Ours mean | Diff |
|---|---|---:|---|---:|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 0.864 (submitted, 3) | 0.600 | 0.600 | -0.264 |

### anthropic/claude-haiku-4-5

| Task | Tier | Ships | Published (reward, end, turns) | r1 | Ours mean | Diff |
|---|---|---:|---|---:|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | – | 0.300 | 0.300 | – |

## Unscored runs

| Sweep | Model | Task | Rep | Attempts | Last outcome | Spend |
|---|---|---|---:|---:|---|---:|
| pilot | openai/gpt-6.1-sol | dock-36A-w15x2-storm-0 | 1 | 3 | no_instance | $1.50 |
| pilot | openai/gpt-6.1-sol | dock-24B-w06x1-busy-0 | 2 | 2 | cost_cap | $0.99 |
| pilot | openai/gpt-6.1-sol | dock-36A-w15x2-storm-0 | 2 | 0 | not run | $0.00 |

## Runs whose agent reward differs from the verifier's

| Sweep | Model | Task | Rep | Agent reward | Verifier reward |
|---|---|---|---:|---:|---:|
| pilot | anthropic/claude-sonnet-5-5 | dock-36A-w15x2-storm-0 | 2 | 0.450 | 0.500 |
"""


def test_the_report_of_a_fixed_set_of_results(pilot):
    assert sweep.report(pilot) == EXPECTED


def test_report_writes_the_markdown_to_out(pilot):
    result = CliRunner().invoke(portsim, ["sweep", "report", "pilot", "extra"])
    assert result.exit_code == 0, result.output
    assert result.output == "Wrote results/parity.md\n"
    assert Path("results/parity.md").read_text() == EXPECTED
    assert CliRunner().invoke(portsim, ["sweep", "report", "pilot", "extra", "--out", "p.md"]).exit_code == 0
    assert Path("p.md").read_text() == EXPECTED
    missing = CliRunner().invoke(portsim, ["sweep", "report", "nope"])
    assert missing.exit_code == 2 and "no sweep 'nope'" in missing.output


def test_g2_is_the_rule_applied_to_the_pack():
    """Ten slots shared by the tiers by largest remainder on 10 x tier size / 50, equal remainders broken in the order
    standard, busy, storm, extreme; then, in each tier sorted by (ships, task id), the task at floor((2i+1)N/(2n)) for
    i < n, the midpoint of each of n equal slices."""
    pack = tasks.pack_tasks("dock-v1-eval")
    size = {tier: sum(t.difficulty == tier for t in pack) for tier in sweep.TIERS}
    assert size == {"standard": 9, "busy": 15, "storm": 13, "extreme": 13}
    quota = {tier: floor(10 * n / len(pack)) for tier, n in size.items()}
    by_remainder = sorted(sweep.TIERS, key=lambda tier: -(10 * size[tier] / len(pack) - quota[tier]))
    for tier in by_remainder[:10 - sum(quota.values())]:
        quota[tier] += 1
    assert quota == {"standard": 2, "busy": 3, "storm": 3, "extreme": 2}
    picked = []
    for tier, n in quota.items():
        ordered = sorted((t for t in pack if t.difficulty == tier), key=lambda t: (len(t.ships), t.task_id))
        picked += [ordered[floor((2 * i + 1) * len(ordered) / (2 * n))].task_id for i in range(n)]
    assert picked == sweep.G2_TASKS


LINES_MODELS = ("| Model | Tasks | Runs scored/planned | Mean reward (95% CI) | Follower reference | Silent reference "
                "| Naive reference | Reached done per rep | Feasible | At the anchor | Mean regret vs anchor "
                "| Mean regret vs hindsight | Mean excused cost | Mean hours at anchor | Messages per episode "
                "| Median turns | Tokens in/out per episode | Cached tokens per episode | Cost per episode | Spend |")
LINES_WEEKS = ("| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | r1 | r2 "
               "| Mean | Regret vs hindsight | Regret vs anchor |")


@pytest.fixture
def lines_pilot(tmp_path, monkeypatch) -> tuple[sweep.Sweep, dict[str, dict]]:
    """A lines sweep: a retry, a week with no scored run, an agent reward that differs, and the lines fields."""
    monkeypatch.chdir(tmp_path)
    a, b, c = sweep.task_ids("all", lines=True)[:3]
    refs = {r["task_id"]: r for r in lines.references()}
    s = sweep.Sweep("lines-pilot", [SONNET, GPT], [a, b, c], 2, 5.0, live=True, lines=True)

    def played(model, task, rep, attempt=1, *, reward=None, over=0, hours=None, messages=None, agent_reward="reward"):
        o = refs[task]["optimal_cost"]
        scored = reward is not None
        return row(s.name, model, task, rep, attempt, reward=reward, plan_cost=o + over, optimal_cost=o,
                   code=None if scored else "provider_error", agent_reward=agent_reward) | {
            "end_reason": "done" if scored else "provider_error", "watches": len(refs[task]["watch_hours"]),
            "excused_cost": 4 if scored else None, "regret": over if scored else None, "anchor_hours": hours,
            "messages": messages}

    write(s, [played(SONNET, a, 1, reward=0.9, over=20, hours=30, messages=12), played(SONNET, a, 2),
              played(SONNET, a, 2, 2, reward=1.0, hours=26, messages=8),
              played(SONNET, b, 1, reward=0.8, over=40, hours=50, messages=4, agent_reward=0.75),
              played(GPT, a, 1, reward=1.0, hours=20, messages=30)])
    return s, refs


def test_the_lines_report_against_the_hindsight_bound_the_anchor_and_the_lines_references(lines_pilot):
    s, refs = lines_pilot
    a, b, c = s.tasks
    text = sweep.lines_report([s])
    found = text.splitlines()
    assert found[:5] == [
        "# PortSim lines: portsim-llm on the wind weeks with the ships' agents", "",
        "Sweeps: `lines-pilot` (anthropic/claude-sonnet-5-5, openai/gpt-6.1-sol; 3 tasks, k=2, episode cap $5).",
        "Harness: portsim-llm, with each ship's agent a portsim-line agent it can message. References, on the same "
        "weeks (data/lines/references.jsonl): hindsight, the clairvoyant CP-SAT optimum that knows every arrival and "
        "slows ships from the first watch it could ask; the anchor that rewards and regret are scored against, the "
        "lower of that cost and the follower's best over its four solver configurations; the follower, in its first "
        "configuration, which re-plans at every watch on the arrivals as known and requests arrival times through the "
        "ships' agents; silent, the same never asking them; and the naive online policy.", ""]
    assert found[5].endswith("Attempts: 5, retries: 1. Unscored runs: 8 of 12.")
    header = found.index(LINES_MODELS)
    assert found[header + 1].count("|") == LINES_MODELS.count("|")

    def mean(xs):
        return f"{statistics.mean(xs):.3f}"

    sonnet = found[header + 2].split(" | ")
    assert sonnet[0] == f"| {SONNET}" and sonnet[1:3] == ["2", "3/6"] and sonnet[3].startswith("0.875 (")
    silent = [refs[t]["silent"] for t in (a, b)]
    assert sonnet[4:] == [
        mean([refs[t]["rolling"]["reward"] for t in (a, b)]), mean([x["reward"] for x in silent if "reward" in x]),
        mean([refs[t]["naive"]["reward"] for t in (a, b)]), "2", "2", "0.5", "20.000",
        mean([refs[t]["optimal_cost"] + over - refs[t]["hindsight_cost"] for t, over in ((a, 20), (a, 0), (b, 40))]),
        "4.000", "35.333", "8.000", "2", "20.0k/5.0k", "0.0k", "$0.1000", "$0.40 |"]
    gpt = found[header + 3].split(" | ")
    assert gpt[1:3] == ["1", "1/6"] and gpt[13:15] == ["20.000", "30.000"]
    assert found.count(LINES_WEEKS) == 2
    weather = {p["task_id"]: f"{p['iso_week']} {p['kind']}" for p in wind.pack().manifest["pairs"]}
    week = lines.pack().get(a)
    ref = refs[a]
    assert (f"| {a} | {weather[a]} | {week.difficulty} | {len(week.ships)} | {len(ref['watch_hours'])} "
            f"| {ref['hindsight_cost']} | {ref['optimal_cost']} (1.000) | {sweep._reference(ref['rolling'])} "
            f"| {sweep._played(ref['silent'])} | {sweep._reference(ref['naive'])} | 0.900 | 1.000 | 0.950 ") in text
    assert "Hindsight as its cost; the anchor and the references as cost (reward)." in found
    unscored = found[found.index("## Unscored runs") + 4:found.index("## Runs whose agent reward differs from the "
                                                                     "verifier's") - 1]
    assert unscored == [f"| lines-pilot | {model} | {t} | {rep} | 0 | not run | $0.00 |" for model, t, rep in (
        (SONNET, c, 1), (SONNET, b, 2), (SONNET, c, 2), (GPT, b, 1), (GPT, c, 1), (GPT, a, 2), (GPT, b, 2),
        (GPT, c, 2))]
    assert text.endswith(f"| lines-pilot | {SONNET} | {b} | 1 | 0.750 | 0.800 |\n")


def test_report_writes_the_lines_report_with_lines_and_refuses_to_mix_it(lines_pilot):
    s, _ = lines_pilot
    result = CliRunner().invoke(portsim, ["sweep", "report", s.name, "--lines"])
    assert result.exit_code == 0, result.output
    assert result.output == "Wrote results/lines.md\n"
    assert Path("results/lines.md").read_text() == sweep.lines_report([s])
    for flags in ([], ["--live"], ["--wind"]):
        refused = CliRunner().invoke(portsim, ["sweep", "report", s.name, *flags])
        assert refused.exit_code == 2 and "lines sweeps: lines-pilot; report them with --lines" in refused.output
    both = CliRunner().invoke(portsim, ["sweep", "report", s.name, "--lines", "--wind"])
    assert both.exit_code == 2 and "--wind and --lines report different envs: pick one" in both.output
