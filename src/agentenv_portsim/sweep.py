"""`agent-env portsim sweep`: dock-v1-eval tasks over models and reps under a spend cap, one `agent-env run` process
per attempt, retried and resumed from results.jsonl; and the report against the published dock-eval50 run.

G2_TASKS is fixed from the pack alone: the tiers share ten slots by largest remainder, and each tier gives the midpoints
of equal slices of its tasks ordered by ship count."""

import json
import random
import re
import signal
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from importlib.resources import files
from pathlib import Path

import click
from agent_env.config import get_config
from agent_env.store.routing import namespace_routing
from agent_env.task.store import get_task_instance_store

from . import tasks

AGENT_ENV = [sys.executable, "-m", "agent_env.cli"]
RUNS = Path("results/runs")
EVAL_PACK = "dock-v1-eval"
PUBLISHED_INDEX = files("agentenv_portsim") / "data/published/dock-eval50/index.json"
NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,40}")
INSTANCE = re.compile(r"(\d+(?:\.\d+)?)s, instance (\S+)")
TIERS = ("standard", "busy", "storm", "extreme")
STOPS = ("model_endpoint", "unpriced_model")
MAX_ATTEMPTS = 3
POLL_SECONDS = 2.0
G2_TASKS = [
    "dock-36A-w35x1-standard-0", "dock-36A-w17x1-standard-0",
    "dock-24B-w06x1-busy-0", "dock-36A-w05x1-busy-0", "dock-36A-w05x2-busy-0",
    "dock-24B-w35x2-storm-0", "dock-24B-w06x2-storm-0", "dock-36A-w15x2-storm-0",
    "dock-24B-w35x2-extreme-1", "dock-36A-w35x2-extreme-0",
]
PUBLISHED = {
    "anthropic/claude-sonnet-5-5": "anthropic:claude-sonnet-5-5",
    "openai/gpt-6.1-sol": "openai:gpt-6.1-sol",
    "fireworks_ai/glm-5p3-flash": "hf:zai-org/GLM-5.3-Flash:baseten",
    "fireworks_ai/qwen3p8-2p4t-a95b": "hf:Qwen/Qwen3.8-2.4T-A95B:together",
    "fireworks_ai/glm-5p3": "hf:zai-org/GLM-5.3:together",
    "groq/qwen3.8-27b": "hf:Qwen/Qwen3.8-27B:cerebras|ovhcloud",
}


@dataclass(frozen=True)
class Sweep:
    name: str
    models: list[str]
    tasks: list[str]
    k: int
    episode_cap_usd: float

    @property
    def out(self) -> Path:
        return RUNS / self.name

    def runs(self) -> list[tuple[str, str, int]]:
        """(model, task, rep), model-major, then rep, then task."""
        return [(m, t, rep) for m in self.models for rep in range(1, self.k + 1) for t in self.tasks]


@dataclass
class Attempt:
    run: tuple[str, str, int]
    number: int
    started_utc: str
    log: Path
    proc: subprocess.Popen

    @property
    def label(self) -> str:
        model, task, rep = self.run
        return f"{model} {task} r{rep} a{self.number}"


def slug(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", model)


def results(out: Path) -> list[dict]:
    path = out / "results.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.is_file() else []


def of(rows: list[dict], run: tuple[str, str, int]) -> list[dict]:
    return [r for r in rows if (r["model"], r["task_id"], r["rep"]) == run]


def final(rows: list[dict]) -> bool:
    """A run is final once scored, stopped at its cost cap, or after MAX_ATTEMPTS counted attempts; an interrupted
    attempt doesn't count."""
    counted = [r for r in rows if r["outcome"] != "interrupted"]
    return (any(r["outcome"] == "scored" or r["error_code"] == "cost_cap" for r in counted)
            or len(counted) >= MAX_ATTEMPTS)


def cost(row: dict, cap: float) -> float:
    """What an attempt spent, or its episode cap when it recorded no spend: the budget counts the worst case."""
    return cap if row["cost_usd"] is None else row["cost_usd"]


def context(instance: str) -> dict:
    with namespace_routing():
        return get_task_instance_store().get(instance).context or {}


def trajectory(uri: str) -> bytes:
    with namespace_routing():
        return get_config().get_object_store_at(uri).get(uri)


def task_ids(spec: str) -> list[str]:
    known = [t.task_id for t in tasks.pack_tasks(EVAL_PACK)]
    if spec == "all":
        return known
    if spec == "g2":
        return G2_TASKS
    ids = spec.split(",")
    if unknown := [i for i in ids if i not in known]:
        raise click.UsageError(f"not {EVAL_PACK} task ids: {', '.join(unknown)}")
    return ids


def prepare(sweep: Sweep) -> None:
    """Writes the sweep's bundle and sweep.json on its first run; a later run must be the same sweep."""
    if not NAME.fullmatch(sweep.name):
        raise click.UsageError("a sweep's name is 1 to 41 lowercase letters, digits and dashes, starting with no dash")
    path = sweep.out / "sweep.json"
    if path.is_file():
        if json.loads(path.read_text()) != asdict(sweep):
            raise click.UsageError(f"{path} is another sweep; run it with its own models, tasks, k and episode cap: "
                                   f"{path.read_text().strip()}")
        return
    tasks.generate(EVAL_PACK, sweep.out / "bundle", task_ids=sweep.tasks, episode_cap_usd=sweep.episode_cap_usd)
    path.write_text(json.dumps(asdict(sweep), indent=2) + "\n")


def preflight(sweep: Sweep, task: str) -> str | None:
    """The problem a dry run of ``task`` finds, as `agent-env run` would before its first step, or None."""
    log = sweep.out / "logs" / "preflight.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w") as f:
        code = subprocess.run([*AGENT_ENV, "run", str((sweep.out / "bundle").absolute()), "--task", task, "--dry-run"],
                              stdout=f, stderr=subprocess.STDOUT).returncode
    return f"the dry run of {task} exited {code}:\n{log.read_text(errors='replace').rstrip()}" if code else None


def start(sweep: Sweep, run: tuple[str, str, int], number: int) -> Attempt:
    model, task, rep = run
    log = sweep.out / "logs" / slug(model) / f"{task}-r{rep}-a{number}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with log.open("w") as f:
        proc = subprocess.Popen([*AGENT_ENV, "run", str((sweep.out / "bundle").absolute()), "--task", task,
                                 "--model", model], stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
    return Attempt(run, number, started, log, proc)


def outcome(sweep: Sweep, attempt: Attempt, earlier: list[dict], interrupted: bool = False, read: bool = True) -> dict:
    """The attempt's row, from the instance its run stored: the verifier's grade and episode, and the play step's
    summary, failure and trajectory. Without ``read`` (the sweep itself failed), from the log alone."""
    model, task, rep = attempt.run
    found = INSTANCE.findall(attempt.log.read_text(errors="replace"))
    wall, instance = (float(found[-1][0]), found[-1][1]) if found else (None, None)
    ctx = context(instance) if instance and read else {}
    m = ctx.get("metadata") or {}
    v = (m.get("verifications") or {}).get("portsim") or {}
    pr = next((p for p in ctx.get("prompt_responses") or [] if p.get("step_id") == "play"), None)
    s = (pr or {}).get("structured_output") or {}
    failed = m.get("failed_steps") or []
    scored = "score" in v
    if s:
        spent = s.get("cost_usd")
    elif instance and not interrupted and pr is None and "play" not in {f["step_id"] for f in failed}:
        spent = 0.0
    else:
        spent = None
    transcript = None
    if pr and pr.get("agent_trajectory_s3_uri"):
        path = sweep.out / "transcripts" / slug(model) / f"{task}-r{rep}-a{attempt.number}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(trajectory(pr["agent_trajectory_s3_uri"]))
        transcript = path.relative_to(sweep.out).as_posix()
    episode = v["results"][0]["episode"] if scored else {}
    grade = episode.get("grade") or {}
    error_code = error = failed_step = None
    if not scored and not interrupted:
        error_code = (pr or {}).get("error_code") or (failed[-1]["error_type"] if failed else "no_instance")
        error = (pr or {}).get("error_message") or (failed[-1]["error"] if failed else None)
        failed_step = failed[-1]["step_id"] if failed else None
    row = {"sweep": sweep.name, "model": model, "task_id": task, "rep": rep, "attempt": attempt.number,
           "started_utc": attempt.started_utc, "wall_seconds": wall, "exit": attempt.proc.returncode,
           "instance": instance, "outcome": "scored" if scored else "interrupted" if interrupted else "failed",
           "failed_step": failed_step, "error_code": error_code, "error": error and error[:500], "retryable": False,
           "reward": v["score"] if scored else None,
           "submitted": episode["end_reason"] == "submitted" if scored else None,
           "feasible": bool(grade.get("feasible")) if scored else None,
           "plan_cost": grade.get("cost"), "optimal_cost": grade.get("optimal_cost"),
           "checks": episode.get("checks_used"), "calls": episode.get("calls_used"),
           **{key: s.get(key) for key in ("end_reason", "turns", "tool_calls", "input_tokens", "output_tokens",
                                          "cached_tokens", "cache_write_tokens")},
           "cost_usd": spent, "agent_reward": s.get("reward"), "transcript": transcript}
    row["retryable"] = not final([*earlier, row])
    return row


def _money(row: dict, cap: float) -> str:
    return f"${row['cost_usd']:.4f}" if row["cost_usd"] is not None else f"no spend recorded, counted as ${cap:.2f}"


def _spend(rows: list[dict], cap: float) -> str:
    unknown = sum(r["cost_usd"] is None for r in rows)
    known = sum(r["cost_usd"] or 0.0 for r in rows)
    return f"${known:.2f} spent" + (f", {unknown} attempts with no spend recorded (${unknown * cap:.2f} at the cap)"
                                    if unknown else "")


def run(sweep: Sweep, cap_usd: float, parallel: int, echo=click.echo) -> int:
    """Plays the runs results.jsonl doesn't hold as final, `parallel` attempts at a time, while the spend so far plus
    the episode cap of every attempt running and the next stays within ``cap_usd``. Returns the exit code: 0 when
    every run is final, 1 when the sweep stopped early, 130 when a signal stopped it. If the sweep itself fails, it
    tears its attempts down and records them from their logs, at their caps, before the error propagates."""
    cap = sweep.episode_cap_usd
    rows = results(sweep.out)
    queue = [r for r in sweep.runs() if not final(of(rows, r))]
    spent = sum(cost(r, cap) for r in rows)
    running: list[Attempt] = []
    stopped = None
    caught: list[int] = []
    previous = {s: signal.signal(s, lambda signum, _: caught.append(signum)) for s in (signal.SIGINT, signal.SIGTERM)}

    def record(attempt: Attempt, interrupted: bool = False, read: bool = True) -> dict:
        nonlocal spent
        row = outcome(sweep, attempt, of(rows, attempt.run), interrupted, read)
        running.remove(attempt)
        rows.append(row)
        spent += cost(row, cap)
        with (sweep.out / "results.jsonl").open("a") as f:
            f.write(json.dumps(row) + "\n")
        return row

    def finish(attempt: Attempt) -> dict:
        row = record(attempt)
        if row["outcome"] == "scored":
            echo(f"done {attempt.label}: reward {row['reward']} ({row['end_reason']}), {_money(row, cap)} "
                 f"(spent ${spent:.2f})")
        else:
            echo(f"failed {attempt.label}: {row['error_code']} {'retry' if row['retryable'] else 'final'} "
                 f"({_money(row, cap)})")
        return row

    def tear_down(read: bool) -> None:
        for attempt in running:
            attempt.proc.terminate()
        for attempt in list(running):
            attempt.proc.wait()
            echo(f"interrupted {attempt.label} ({_money(record(attempt, interrupted=True, read=read), cap)})")

    try:
        if queue:
            stopped = preflight(sweep, queue[0][1])
        while not caught and (running or (queue and not stopped)):
            while (queue and not stopped and len(running) < parallel
                   and spent + (len(running) + 1) * cap <= cap_usd + 1e-9):
                r = queue.pop(0)
                attempt = start(sweep, r, len(of(rows, r)) + 1)
                running.append(attempt)
                echo(f"start {attempt.label} (spent ${spent:.2f} of ${cap_usd:.2f})")
            if not running:
                stopped = (f"another attempt could take the spend past ${cap_usd:.2f} (${spent:.2f} spent, "
                           f"${cap:.2f} an attempt at most); {len(queue)} runs not final")
                break
            time.sleep(POLL_SECONDS)
            for attempt in [a for a in running if a.proc.poll() is not None]:
                row = finish(attempt)
                if row["error_code"] in STOPS:
                    stopped = f"{row['error_code']} from {attempt.label}: {row['error']}"
                elif row["retryable"]:
                    queue.append(attempt.run)
        if caught:
            for attempt in [a for a in running if a.proc.poll() is not None]:
                finish(attempt)
            tear_down(read=True)
            return 130
    except BaseException:
        tear_down(read=False)
        raise
    finally:
        for s, handler in previous.items():
            signal.signal(s, handler)
    for model in sweep.models:
        planned = [r for r in sweep.runs() if r[0] == model]
        scored = sum(any(x["outcome"] == "scored" for x in of(rows, r)) for r in planned)
        unscored = sum(final(of(rows, r)) for r in planned) - scored
        echo(f"{model}: {scored} scored, {unscored} unscored, {len(planned) - scored - unscored} not final, of "
             f"{len(planned)} runs; {_spend([x for x in rows if x['model'] == model], cap)}")
    if stopped:
        echo(f"stopped: {stopped}")
    return 0 if all(final(of(rows, r)) for r in sweep.runs()) else 1


def ci(xs, n=2000, seed=0):
    rng = random.Random(seed)
    means = sorted(statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n)]


def load(name: str) -> Sweep:
    path = RUNS / name / "sweep.json"
    if not path.is_file():
        raise click.UsageError(f"no sweep {name!r}: {path} doesn't exist")
    return Sweep(**json.loads(path.read_text()))


def _with_ci(xs: list[float], f: str = ".3f") -> str:
    if not xs:
        return "–"
    lo, hi = ci(xs)
    return f"{statistics.mean(xs):{f}} ({lo:{f}} to {hi:{f}})"


def _mean(xs: list[float]) -> str:
    return f"{statistics.mean(xs):.3f}" if xs else "–"


def _count(x: float) -> str:
    return f"{x:.1f}".removesuffix(".0")


def _tokens(episodes: list[dict]) -> str:
    pairs = [(e["input_tokens"], e["output_tokens"]) for e in episodes if e["input_tokens"] is not None]
    return (f"{statistics.mean(i for i, _ in pairs) / 1000:.1f}k/{statistics.mean(o for _, o in pairs) / 1000:.1f}k"
            if pairs else "–")


def _optimal(e: dict, cost_key: str) -> bool:
    return bool(e["feasible"]) and e[cost_key] == e["optimal_cost"]


def _per_rep(by_task: dict[str, list[dict]], count) -> float:
    """How many tasks a pass counts, the mean over each task's scored reps."""
    return sum(statistics.mean(bool(count(r)) for r in rs) for rs in by_task.values())


class Pooled:
    """The named sweeps' runs pooled per model and task, next to the published episodes of the same tasks."""

    def __init__(self, sweeps: list[Sweep]):
        self.sweeps = sweeps
        self.pack = {t.task_id: t for t in sorted(tasks.pack_tasks(EVAL_PACK), key=lambda t: t.task_id)}
        self.index = json.loads(PUBLISHED_INDEX.read_text())
        self.published = {(e["model"], e["task_id"]): e for e in self.index["episodes"]}
        rows = {s.name: results(s.out) for s in sweeps}
        self.caps = {s.name: s.episode_cap_usd for s in sweeps}
        self.runs = {(s.name, *run): of(rows[s.name], run) for s in sweeps for run in s.runs()}
        self.scored = {key: next((r for r in rs if r["outcome"] == "scored"), None) for key, rs in self.runs.items()}
        self.models = list(dict.fromkeys(m for s in sweeps for m in s.models))

    def by_task(self, model: str) -> dict[str, list[dict]]:
        """Each task's scored runs, for the tasks with one, by task id: the order upstream's bootstrap draws from."""
        found = {t: [row for key, row in self.scored.items() if key[1:3] == (model, t) and row] for t in self.pack}
        return {t: rs for t, rs in found.items() if rs}

    def episodes(self, model: str, task_ids) -> list[dict] | None:
        spec = PUBLISHED.get(model)
        return [self.published[spec, t] for t in task_ids] if spec else None

    def spend(self, rows: list[tuple[str, dict]]) -> tuple[float, int, float]:
        """Known spend, attempts with none recorded, and those at their cap."""
        unknown = [(name, r) for name, r in rows if r["cost_usd"] is None]
        return (sum(r["cost_usd"] or 0.0 for _, r in rows), len(unknown),
                sum(self.caps[name] for name, _ in unknown))

    def attempts(self, model: str | None = None) -> list[tuple[str, dict]]:
        return [(key[0], r) for key, rs in self.runs.items() for r in rs if model in (None, key[1])]

    def header(self) -> list[str]:
        known, unknown, at_cap = self.spend(self.attempts())
        attempts = len(self.attempts())
        unscored = sum(row is None for row in self.scored.values())
        return [
            "# PortSim parity: portsim-llm against the published dock-eval50 run", "",
            "Sweeps: " + "; ".join(f"`{s.name}` ({', '.join(s.models)}; {len(s.tasks)} tasks, k={s.k}, episode cap "
                                   f"${s.episode_cap_usd:g})" for s in self.sweeps) + ".",
            f"Harness: portsim-llm. Published: {self.index['run']} @ b0f4c2f, {len(self.index['episodes'])} episodes.",
            "",
            f"Spend: ${known:.2f} known; {unknown} attempts with no spend recorded, ${at_cap:.2f} at the cap. "
            f"Attempts: {attempts}, retries: {attempts - sum(bool(rs) for rs in self.runs.values())}. "
            f"Unscored runs: {unscored} of {len(self.runs)}.",
        ]

    def model_line(self, model: str) -> str:
        by_task = self.by_task(model)
        ours = {t: statistics.mean(r["reward"] for r in rs) for t, rs in by_task.items()}
        rows = [r for rs in by_task.values() for r in rs]
        pub = self.episodes(model, ours)
        turns = [r["turns"] for r in rows if r["turns"] is not None]
        costs = [r["cost_usd"] for r in rows if r["cost_usd"] is not None]
        known, unknown, _ = self.spend(self.attempts(model))
        if pub is None:
            pub_mean = diff = pub_submitted = pub_feasible = pub_optimal = pub_turns = pub_tokens = "–"
        else:
            pub_mean = _with_ci([e["reward"] for e in pub])
            diff = _with_ci([ours[t] - e["reward"] for t, e in zip(ours, pub, strict=True)], "+.3f")
            pub_submitted, pub_feasible = str(sum(e["submitted"] for e in pub)), str(sum(e["feasible"] for e in pub))
            pub_optimal = str(sum(_optimal(e, "cost") for e in pub))
            pub_turns = f"{statistics.median(e['turns'] for e in pub):g}" if pub else "–"
            pub_tokens = _tokens(pub)
        return "| " + " | ".join([
            model, PUBLISHED.get(model, "–"), str(len(ours)),
            f"{len(rows)}/{sum(key[1] == model for key in self.runs)}", _with_ci(list(ours.values())), pub_mean, diff,
            f"{_count(_per_rep(by_task, lambda r: r['submitted']))} / {pub_submitted}",
            f"{_count(_per_rep(by_task, lambda r: r['feasible']))} / {pub_feasible}",
            f"{_count(_per_rep(by_task, lambda r: _optimal(r, 'plan_cost')))} / {pub_optimal}",
            f"{statistics.median(turns):g} / {pub_turns}" if turns else f"– / {pub_turns}",
            f"{_tokens(rows)} vs {pub_tokens}",
            f"${statistics.mean(costs):.4f}" if costs else "–",
            f"${known:.2f}" + (f" + {unknown} unknown" if unknown else ""),
        ]) + " |"

    def tier_line(self, model: str) -> str:
        ours = {t: statistics.mean(r["reward"] for r in rs) for t, rs in self.by_task(model).items()}
        cells = []
        for tier in TIERS:
            mine = [t for t in ours if self.pack[t].difficulty == tier]
            pub = self.episodes(model, mine)
            published = "–" if pub is None else _mean([e["reward"] for e in pub])
            cells.append(f"{_mean([ours[t] for t in mine])} / {published}" if mine else "–")
        return f"| {model} | " + " | ".join(cells) + " |"

    def weeks(self, model: str) -> list[str]:
        spec = PUBLISHED.get(model)
        mine = [s for s in self.sweeps if model in s.models]
        reps = [(s.name, rep) for s in mine for rep in range(1, s.k + 1)]
        lines = ["", f"### {model}", "",
                 "| Task | Tier | Ships | Published (reward, end, turns) | "
                 + " | ".join(f"r{i}" for i in range(1, len(reps) + 1)) + " | Ours mean | Diff |",
                 "|---|---|---:|---|" + "---:|" * (len(reps) + 2)]
        for t in [t for t in self.pack if any(t in s.tasks for s in mine)]:
            e = self.published.get((spec, t))
            values = [self.scored.get((name, model, t, rep)) for name, rep in reps]
            rewards = [v["reward"] for v in values if v]
            ours = statistics.mean(rewards) if rewards else None
            lines.append(" | ".join([
                f"| {t}", self.pack[t].difficulty, str(len(self.pack[t].ships)),
                f"{e['reward']:.3f} ({e['end_reason']}, {e['turns']})" if e else "–",
                *(f"{v['reward']:.3f}" if v else "–" for v in values),
                "–" if ours is None else f"{ours:.3f}",
                f"{ours - e['reward']:+.3f}" if ours is not None and e else "–",
            ]) + " |")
        return lines

    def unscored(self) -> list[str]:
        keys = [key for key, row in self.scored.items() if row is None]
        if not keys:
            return ["None."]
        lines = ["| Sweep | Model | Task | Rep | Attempts | Last outcome | Spend |", "|---|---|---|---:|---:|---|---:|"]
        for key in keys:
            rs = self.runs[key]
            last = (rs[-1]["error_code"] or rs[-1]["outcome"]) if rs else "not run"
            spent = sum(cost(r, self.caps[key[0]]) for r in rs)
            lines.append(f"| {key[0]} | {key[1]} | {key[2]} | {key[3]} | {len(rs)} | {last} | ${spent:.2f} |")
        return lines

    def differs(self) -> list[str]:
        found = [(key, row) for key, row in self.scored.items()
                 if row is not None and (row["agent_reward"] or 0.0) != row["reward"]]
        if not found:
            return ["None."]
        return ["| Sweep | Model | Task | Rep | Agent reward | Verifier reward |", "|---|---|---|---:|---:|---:|"] + [
            f"| {key[0]} | {key[1]} | {key[2]} | {key[3]} | "
            f"{'–' if row['agent_reward'] is None else format(row['agent_reward'], '.3f')} | {row['reward']:.3f} |"
            for key, row in found]


def report(sweeps: list[Sweep]) -> str:
    """results/parity.md: each model's scored runs against the published dock-eval50 episodes of the same tasks. A
    task's value is the mean of its scored reps across the sweeps; the CIs bootstrap over tasks, as upstream's do."""
    pooled = Pooled(sweeps)
    lines = [*pooled.header(), "", "## Per model", "",
             "| Model | Published as | Tasks | Runs scored/planned | Ours mean (95% CI) "
             "| Published mean on these tasks (95% CI) | Mean diff ours−published (95% CI) "
             "| Submitted per rep / published | Feasible | Optimal | Median turns ours/published "
             "| Tokens in/out per episode ours/published | Cost per episode | Spend |",
             "|---|---|---:|---:|---|---|---|---:|---:|---:|---:|---|---:|---:|",
             *(pooled.model_line(m) for m in pooled.models),
             "", "## Per tier", "", "Mean reward over each tier's tasks, ours / published.", "",
             "| Model | " + " | ".join(TIERS) + " |", "|---|" + "---:|" * len(TIERS),
             *(pooled.tier_line(m) for m in pooled.models),
             "", "## Week by week", *(line for m in pooled.models for line in pooled.weeks(m)),
             "", "## Unscored runs", "", *pooled.unscored(),
             "", "## Runs whose agent reward differs from the verifier's", "", *pooled.differs()]
    return "\n".join(lines) + "\n"


@click.group("sweep")
def sweep_group():
    """Sweeps: dock-v1-eval tasks over models and reps under a spend cap, and the parity report."""


@sweep_group.command("run")
@click.option("--name", required=True, help="The sweep's name: its results go to results/runs/<name>/.")
@click.option("--models", required=True, help="Comma-separated LiteLLM model ids, e.g. anthropic/claude-sonnet-5-5.")
@click.option("--tasks", "task_spec", required=True, help="all, g2, or comma-separated dock-v1-eval task ids.")
@click.option("--cap-usd", type=float, required=True,
              help="The model spend the sweep stays within: no attempt starts that could take it past this at the "
                   "episode cap.")
@click.option("--k", type=click.IntRange(min=1), default=1, show_default=True, help="Reps of each model and task.")
@click.option("--episode-cap-usd", type=float, default=5.0, show_default=True,
              help="An episode's cost cap, passed to the agent as PORTSIM_MAX_COST_USD.")
@click.option("--parallel", type=click.IntRange(min=1), default=4, show_default=True, help="Attempts at a time.")
def run_command(name: str, models: str, task_spec: str, cap_usd: float, k: int, episode_cap_usd: float,
                parallel: int):
    """Play each model on each task k times, one `agent-env run` per attempt, logged under results/runs/<name>/logs.
    Each attempt is a line of results.jsonl; a failed one is retried up to twice, and running the sweep again plays
    the runs that aren't final yet. Ctrl-C tears the running attempts down."""
    if "" in models.split(","):
        raise click.UsageError("--models takes comma-separated model ids, none empty")
    sweep = Sweep(name, models.split(","), task_ids(task_spec), k, episode_cap_usd)
    prepare(sweep)
    raise SystemExit(run(sweep, cap_usd, parallel))


@sweep_group.command("report")
@click.argument("names", nargs=-1, required=True)
@click.option("--out", type=click.Path(dir_okay=False, path_type=Path), default=Path("results/parity.md"),
              show_default=True, help="The Markdown file to write.")
def report_command(names: tuple[str, ...], out: Path):
    """Compare the sweeps NAMES with the published dock-eval50 run, per model, tier and week."""
    text = report([load(name) for name in names])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    click.echo(f"Wrote {out}")
