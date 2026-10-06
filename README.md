# PortSimEnv for AgentEnv

[![CI](https://github.com/earakely-scale/agentenv-portsim-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/earakely-scale/agentenv-portsim-plugin/actions/workflows/ci.yml)
[![License: Apache-2.0, data CC BY-SA 4.0](https://img.shields.io/badge/license-Apache--2.0%20%C2%B7%20data%20CC%20BY--SA%204.0-blue)](NOTICE)
[![Built on the AgentEnv Framework](https://img.shields.io/badge/built%20on-AgentEnv%20Framework-6f42c1)](https://www.agentenvframework.com)

An agent gets one container quay at the Port of Barcelona, the ships that really called there in a week of 2024, and a
week that has just gone wrong: late and bunched ships, closed quay sections, crane breakdowns, gales, emergencies. It
decides when, where and with how many cranes every ship docks, and its plan is graded once, deterministically,
against a plan CP-SAT proved optimal.

**PortSimEnv is Adithya S Kolavi's environment, from [FineEnvs](https://github.com/adithya-s-k/FineEnvs).** Read
the article, [Simulation RL Environments, part 1](https://huggingface.co/spaces/FineEnvs/simulation-rl-environments);
play an episode in the [PortSimEnv Space](https://huggingface.co/spaces/FineEnvs/PortSimEnv); watch the published
eval rollouts in 3D in the [eval Space](https://huggingface.co/spaces/FineEnvs/PortSimEnv-Eval); get the tasks and
rollouts from the [dataset](https://huggingface.co/datasets/FineEnvs/PortSimEnv); and read the
[code](https://github.com/adithya-s-k/FineEnvs/tree/b0f4c2f9526e3c45d608b4f92f6ec6c71fecc152/07-simulation-environments/portsim-v1).

This repository is an environment plugin that runs PortSimEnv v1 in the
[AgentEnv Framework](https://www.agentenvframework.com), Scale AI's open-source framework for building RL
environments, at parity with upstream: the same tools, the same tasks and the same reward for the same plan. Upstream's
agent harness comes along as the A2A agent `portsim-llm`, so a model plays the 50 eval tasks as it did in the
published eval. A live port is next.

**Contents:** [Parity](#parity-with-portsimenv) · [Run it yourself](#run-it-yourself) · [Tasks](#tasks) ·
[Play a model](#play-a-model) · [The environment](#the-environment) · [Grading](#grading) ·
[Built on the AgentEnv Framework](#built-on-the-agentenv-framework) · [Layout](#repository-layout) ·
[Development](#development) · [Licence and credits](#licence-and-credits)

## Parity with PortSimEnv

The goal is the same environment, not a look-alike. An agent sees what it would see upstream and gets the same reward
for the same plan:

- **The same tools.** `get_situation`, `check_plan(plan)` and `submit_plan(plan)` keep upstream's names,
  descriptions and input schemas, return the same text, fail with the same errors and keep the same limits: 10 checks
  and 24 tool calls an episode.
- **The same tasks.** The dock-v1-eval (50) and dock-v1-train (1,050) task packs, byte for byte; any of the 1,100
  loads by id.
- **The same reward for the same plan.** The grader is upstream's `berth_core`, copied unchanged.

The tests check this without calling any model:

1. **Regrade.** The 202 final plans submitted in the published eval grade to their published reward, and every
   task's stored optimal plan grades to 1.0.
2. **Replay.** The 830 tool calls of the 300 published episodes, from the
   [dataset](https://huggingface.co/datasets/FineEnvs/PortSimEnv) at a pinned revision, go through this env's MCP
   tools in order, and each output must equal the recorded one byte for byte; one recorded output that differs is
   allow-listed.
3. **Goldens.** What the episodes never reach (the tool list, the 11th check, the 24-call limit, calls after a
   submit) is compared the same way against outputs recorded from upstream's env (`scripts/record_goldens.py`).
4. **Wiring.** The three [tasks](#tasks) run through `agent-env` and score as expected; CI runs them on every change.
5. **Harness.** `portsim-llm` plays five published episodes, on all three model APIs, against a stand-in model
   server that answers with the recorded turns. The messages and steps it records must equal the published ones,
   its requests must equal those upstream's harness sends for the same turns (`scripts/record_harness.py`), and each
   episode must end with its published reward.

Whether a model scores here as it did upstream is a separate question, answered week by week rather than by a pass
test: see [The comparison with the published eval](#the-comparison-with-the-published-eval), which is pending.

What differs is how the env is served, not what the agent sees:

- **Transport.** Upstream serves its tools through OpenEnv, where an episode runs over a WebSocket session. Here an
  AgentEnv env server serves them over MCP (streamable HTTP at `/mcp`), one episode per container.
- **Choosing a task.** Upstream's `reset(task_id=...)` is the extension `urn:portsim:load-task/v1`, which a task
  applies with `apply_server_config`.
- **Reading the grade.** The env grades the plan once, at submit, and keeps the reward `submit_plan` returns, for the
  plan as validated against the tool's input schema (a ship id sent as `3.0` is ship 3); the task's verifier reads it
  from `data/get`.
- **Not here:** the 3D viewer, the web UI and the task API. Play and watch episodes in upstream's Spaces.

## Run it yourself

You need [Docker](https://docs.docker.com/get-docker/), running and usable without `sudo`, with its buildx plugin,
[uv](https://docs.astral.sh/uv/) and git. No model key: the tasks in the bundle call no model.

```bash
git clone https://github.com/earakely-scale/agentenv-portsim-plugin
uv tool install agentenv-framework --with-editable ./agentenv-portsim-plugin
cd agentenv-portsim-plugin

cp .agentenv/config.example.toml .agentenv/config.toml   # the local profile
agent-env portsim setup              # build the env image for this machine and register it as the env "portsim"
agent-env run portsim --task smoke   # load a task, submit its optimal plan, grade it
```

The run prints `tasks/smoke.json v1: passed` with the score (1), the time and the instance id; the run and its grade
are stored under `~/.local/state/agent-env`. Run `agent-env` from inside the checkout, so it reads
`.agentenv/config.toml`.

`setup` builds for the Docker host's own platform (`linux/arm64` on Apple Silicon). For Modal, switch
`.agentenv/config.toml` to the `modal_vm` profile it describes, set its `repository_prefix` to your own GHCR
namespace, and run `agent-env portsim setup --platform linux/amd64`, which pushes the image to
`ghcr.io/<namespace>/agentenv-portsim-env`. In an existing agent-env install, `agent-env plugin add
./agentenv-portsim-plugin` adds the plugin.

<details>
<summary>Troubleshooting</summary>

- **`agent-env: command not found`:** uv installed it in a directory that isn't on your PATH yet; run
  `uv tool update-shell` and open a new terminal.
- **A step fails because something holds port 5000:** agent-env keeps its images in a local registry on
  `127.0.0.1:5000`. On macOS, AirPlay Receiver often holds that port; turn it off in System Settings.
- **The run says there is no env `portsim`:** run `agent-env portsim setup` first, with the same config.
</details>

## Tasks

The bundle `portsim` holds three wiring tasks. Each deploys the env, loads a task with `urn:portsim:load-task/v1`
and is graded by `portsim-verifier`:

| Task | What it does | Score |
|---|---|---|
| `smoke` | submits the task's optimal plan through `urn:portsim:submit-plan/v1` | 1, so it prints `passed` |
| `wiring-infeasible` | submits a plan that breaks the rules | at most 0.2 |
| `wiring-nosubmit` | submits nothing | 0 |

```bash
agent-env run portsim --task smoke --task wiring-infeasible --task wiring-nosubmit
```

The env holds both of upstream's dock-v1 packs, built from the port's 2024 container calls at quays 24B (APM
Terminals Barcelona) and 36A (Terminal Catalunya, BEST):

| Pack | Tasks | Tiers | Ships |
|---|---:|---|---|
| dock-v1-eval | 50 | standard 9, busy 15, storm 13, extreme 13 | 14 to 59 |
| dock-v1-train | 1,050 | standard 266, busy 260, storm 262, extreme 262 | 12 to 90 |

Ids read `dock-<quay>-w<week>x<weeks>-<tier>-<seed>`, e.g. `dock-24B-w07x1-busy-0`. No week appears in both packs.
To put a model on them, see [Play a model](#play-a-model).

## Play a model

`portsim-llm` (`agents/portsim-llm/agent.py`) is upstream's harness loop as an A2A agent. It keeps upstream's system
prompt and opening message, its nudges, notes and limits (12 turns, 32,000 output tokens a turn) and the episode
record upstream publishes, and it calls each model on the API upstream used for its provider, through agent-env's
model endpoint, a [LiteLLM](https://docs.litellm.ai/) proxy:

| Model id | API |
|---|---|
| `anthropic/...` | Messages, streamed |
| `openai/...` | Responses, streamed, with encrypted reasoning, effort `medium` and summary `auto` |
| any other | chat completions, streamed |

You need a LiteLLM proxy and a key for it. Name them in `.agentenv/config.toml`, or set `LITELLM_BASE_URL` and
`LITELLM_API_KEY`:

```toml
[model]
base_url = "https://your-litellm-proxy"
api_key  = "secret:PORTSIM_MODEL_KEY"   # read through [stores.secret]; the local store takes it from the env var
```

Then build both images, write the eval tasks and play one:

```bash
agent-env portsim setup --agent                        # the env and portsim-llm, for this machine
agent-env portsim tasks generate --pack dock-v1-eval   # 50 tasks in results/bundles/dock-v1-eval
agent-env run results/bundles/dock-v1-eval --task dock-24B-w06x1-busy-0 --model anthropic/claude-sonnet-5-5
```

Each task deploys the env, loads its PortSim task, deploys `portsim-llm`, plays one episode and grades the plan with
`portsim-verifier`. A task names no model; `--model` picks it.

What differs from upstream's harness:

- **The env** is reached over MCP. MCP has no done flag, so the episode ends when `submit_plan` reports
  `"submitted": true` or after the 24th call.
- **One endpoint.** Upstream's chains of fallback providers are gone; every model goes through the proxy.
- **Cost.** Each turn's token usage is priced from a table pinned in the agent, which holds
  `anthropic/claude-sonnet-5-5`, `openai/gpt-6.1-sol` and `fireworks_ai/glm-5p3-flash`; any other model fails before
  its first request. A request whose usage never arrives (it failed, or the harness cut its stream) is charged the most
  it could have cost. The episode stops before a request that could take its spend past `PORTSIM_MAX_COST_USD` ($5 in
  the generated tasks).
- **Failures.** A model error after the SDK's retries, an env error, a turn that would start after the task's two
  hours, or the cost cap fails the run as an infrastructure error, with the episode so far, instead of scoring it.

A sweep plays models over tasks and reps under a spend cap, and reports them against the published eval:

```bash
agent-env portsim sweep run --name pilot --models anthropic/claude-sonnet-5-5,openai/gpt-6.1-sol --tasks g2 \
    --cap-usd 20
agent-env portsim sweep report pilot   # results/parity.md
```

- Each attempt is its own `agent-env run` process. Its log, its row in `results.jsonl` and the agent's transcript go
  to `results/runs/<name>/`.
- `--tasks` takes `all`, `g2` or task ids; `g2` is the ten weeks of
  [the comparison](#the-comparison-with-the-published-eval).
- An attempt starts only if the spend so far plus the episode cap (`--episode-cap-usd`, default $5) of every attempt
  running, the new one included, stays within `--cap-usd`. An attempt whose spend isn't known counts at its cap.
- A failed attempt is retried up to twice; an episode stopped at its cost cap is not. Running the same sweep again
  resumes it. Ctrl-C, or an error in the sweep itself, tears the running attempts down and records them.
- `report` compares each model with its episodes in the published dock-eval50 run (`data/published/`) on the same
  tasks: means with upstream's bootstrap CIs, the difference per task, per tier and week by week, with submitted,
  feasible and optimal counts, turns, tokens and cost.

### The comparison with the published eval

The comparison plays `portsim-llm` with the published closed models, `openai/gpt-6.1-sol` and
`anthropic/claude-sonnet-5-5`, on ten eval weeks, and sets each week's reward next to the published one. It reports
the differences without a pass or fail line. **It is pending: no results are published here yet.**

The ten weeks (`--tasks g2`) were fixed from the pack alone, before any model played them:

1. The tiers share the ten slots in proportion to their size, by largest remainder (ties in the order standard, busy,
   storm, extreme): standard 2, busy 3, storm 3, extreme 2.
2. A tier of N tasks, sorted by (ships, task id), gives its n weeks at positions ⌊(2i+1)·N/(2n)⌋ for i = 0…n−1: the
   middle task of each of n equal slices of that order.

| Tier | Weeks (ships) |
|---|---|
| standard | `dock-36A-w35x1-standard-0` (19), `dock-36A-w17x1-standard-0` (29) |
| busy | `dock-24B-w06x1-busy-0` (17), `dock-36A-w05x1-busy-0` (27), `dock-36A-w05x2-busy-0` (51) |
| storm | `dock-24B-w35x2-storm-0` (24), `dock-24B-w06x2-storm-0` (32), `dock-36A-w15x2-storm-0` (56) |
| extreme | `dock-24B-w35x2-extreme-1` (25), `dock-36A-w35x2-extreme-0` (39) |

Both quays are in it: four weeks at 24B and six at 36A. `tests/sweep/` recomputes the list from the pack.

## The environment

`PortSimEnv` (`src/agentenv_portsim/server.py`) serves upstream's three tools:

| Tool | What it does |
|---|---|
| `get_situation()` | The quay, notices, ships already alongside, closed sections, cranes, wind windows and the table of ships to berth, as Markdown. It still answers after the episode ends |
| `check_plan(plan)` | Rule violations, departure, delay and cost per ship, and the plan's cost, as JSON with `checks_left`. 10 an episode; it doesn't grade the plan |
| `submit_plan(plan)` | Grades the plan and ends the episode: `submitted`, `feasible` and `reward`, then the cost, delay cost and moves of a valid plan, or the violations of one that isn't |

A plan has one entry per ship, `[{"ship": 0, "berth_hour": 36, "section": 22, "cranes": 3}, ...]`, where `cranes`
defaults to the ship's planned cranes; it can also be sent as a string. Every tool call counts toward the limit of
24, failed ones included, and a 24th call that isn't a submit ends the episode with reward 0. Once the episode is
over, `check_plan` and `submit_plan` return an error.

For the harness, not the agent:

| Surface | What it does |
|---|---|
| `urn:portsim:load-task/v1` `{"task_id": ...}` | Loads the task and resets the counters; an unknown id is an error |
| `urn:portsim:submit-plan/v1` `{"plan": ...}` | Does what `submit_plan` does; the wiring tasks use it |
| `data/reset` | Clears the episode |
| `data/get` | `task_id`, `checks_used`, `calls_used`, `done`, `end_reason`, `plan`, `grade` and `reward`; never the task's reference plans (the grade, there only after a submit, includes the optimal and naive costs) |

## Grading

The env grades a submitted plan once, with `berth_core`'s reward v3, which every dock-v1 task uses:

- A plan that breaks any rule, or has entries the checker can't use, scores 0.2 times the fraction of clean ships,
  so less than 0.2.
- A valid plan scores 0.2 + 0.8·e^(−g/0.5), with g = max(0, cost − optimum) / (max(0, optimum − floor) + 100). The
  optimum is the cost of the CP-SAT plan and the floor the cost no plan can avoid, so the optimum scores 1.0.
- An episode that ends without a submit scores 0.

Rewards are rounded to six decimals, and the same plan always gets the same reward. `portsim-verifier` reads
`data/get` and reports one row whose score is the reward, so with `weighted_average` the task's score is the reward
itself. If the env can't answer `data/get`, the verifier raises and the run fails rather than scoring 0.
`agent-env run` prints `passed` only for a score of 1; any other reward prints `scored below 1` with the score.

## Built on the AgentEnv Framework

This plugin is built on the [AgentEnv Framework](https://www.agentenvframework.com)
([GitHub](https://github.com/scaleapi/agentenv-framework), `pip install agentenv-framework`). The framework does the
heavy lifting; this repository adds PortSimEnv. Each piece maps to a framework concept:

| AgentEnv concept | Here |
|---|---|
| [Environment](https://www.agentenvframework.com/docs/environments/creating): MCP tools, a data plane and extensions in one container | `src/agentenv_portsim/server.py`, an `AgentEnvEnvironment` with three tools, `data/reset` and `data/get`, and two extensions |
| [Plugin](https://www.agentenvframework.com/docs/plugins/environment-plugins): a pip package with entry points | `pyproject.toml`: the bundle (`agent_env.bundles`) and the `agent-env portsim` commands (`agent_env.cli_plugins`) |
| [Tasks](https://www.agentenvframework.com/docs/tasks/creating) and verifiers | `src/agentenv_portsim/bundles/portsim/`: the wiring tasks and `portsim-verifier`, run with `agent-env run portsim --task <task>`; `agent-env portsim tasks generate` writes a pack's tasks as a folder bundle |
| [A2A agent](https://www.agentenvframework.com/docs/agents/creating): an agent in a container, on agent-env's model endpoint | `agents/portsim-llm/`, an `AgentEnvAgent` that reads the env's MCP server from the task and returns its episode as the trajectory |
| [Registry](https://www.agentenvframework.com/docs/registry): versioned images, envs, agents and runs | `agent-env portsim setup` builds the image `agentenv-portsim-env` and registers the env `portsim`, and with `--agent` the agent `portsim-llm`; every run and grade is stored |

## Repository layout

```
src/agentenv_portsim/   the env (server.py), the agent-env portsim commands (cli.py), the eval tasks (tasks.py)
                        and the sweep and its report (sweep.py)
  bundles/portsim/      the wiring tasks and portsim-verifier
src/berth_core/         PortSimEnv's core: tasks, checker, reward, prompts; copied unchanged (VENDORED.md)
agents/portsim-llm/     the portsim-llm agent and its image
data/                   the dock-v1-eval and dock-v1-train task packs, and the published dock-eval50 results in
                        published/, copied unchanged (CC BY-SA 4.0)
tests/                  env, agent, packaging, replay, golden and sweep tests; fake_litellm.py stands in for the
                        model endpoint
scripts/                record_goldens.py, record_harness.py, replay_episode.py
Dockerfile              the env image
```

## Development

```bash
uv venv && uv pip install -e '.[dev]'
.venv/bin/pytest                         # sets BERTH_TASKS_DIR itself; calls no model
.venv/bin/ruff check .
docker build -t agentenv-portsim-env .   # the env image, for this machine's platform
.venv/bin/python -m agentenv_portsim.server   # on :18765, with the packs in data/
```

`scripts/replay_episode.py` plays a published episode through `agent-env run` on local Docker with no model spend:
the stand-in model server answers `portsim-llm` with the recorded turns, and the task must score the published reward.

```bash
agent-env portsim setup --agent && agent-env portsim tasks generate --pack dock-v1-eval
PYTHONPATH=tests .venv/bin/python scripts/replay_episode.py --bundle results/bundles/dock-v1-eval \
    --task dock-24B-w06x1-busy-0 --published anthropic:claude-sonnet-5-5 --model anthropic/claude-sonnet-5-5
```

CI (`.github/workflows/ci.yml`) lints, runs the tests on Python 3.11 and 3.12 and `agent-env plugin check`, then
builds both images, runs the three wiring tasks, checks the 50 eval tasks with a dry run, and runs the golden, replay
and harness tests against the env image (`PORTSIM_URL`).
Contributions are welcome; [CONTRIBUTING.md](CONTRIBUTING.md) covers how a change gets in and what must not change.

## Licence and credits

The code is licensed under the Apache License 2.0 ([LICENSE](LICENSE), [NOTICE](NOTICE)); the data is CC BY-SA 4.0.
The wheel and the env image carry both, so the package's licence is `Apache-2.0 AND CC-BY-SA-4.0`.

- **[PortSimEnv v1](https://github.com/adithya-s-k/FineEnvs/tree/b0f4c2f9526e3c45d608b4f92f6ec6c71fecc152/07-simulation-environments/portsim-v1)**
  is by Adithya S Kolavi, part of [FineEnvs](https://github.com/adithya-s-k/FineEnvs), under the Apache License
  2.0. `src/berth_core/` is copied from it unchanged at commit `b0f4c2f` ([VENDORED.md](VENDORED.md)), the env's
  tools are ported from its OpenEnv server, and `portsim-llm` is ported from its agent harness.
- **The task packs** in `data/` were built by Adithya S Kolavi from the Port of Barcelona's 2024 container calls and
  are licensed under CC BY-SA 4.0 ([data/LICENSE](data/LICENSE)). Contains data from the Port de Barcelona open data
  portal. `tests/golden/` and the plans in the bundle's tasks are derived from them, under the same licence.
- **The published episodes** the replay and harness tests read come from the
  [PortSimEnv dataset](https://huggingface.co/datasets/FineEnvs/PortSimEnv) (CC BY-SA 4.0), fetched at a pinned
  revision and never stored here. The published dock-eval50 results that `sweep report` compares with,
  `data/published/dock-eval50/index.json`, are copied unchanged from upstream's repository, under the same licence.
- **[AgentEnv Framework](https://www.agentenvframework.com)**
  ([scaleapi/agentenv-framework](https://github.com/scaleapi/agentenv-framework)) runs the tasks and the registry this
  plugin plugs into.

This plugin is independent: neither the Port de Barcelona nor PortSimEnv's author is affiliated with it or endorses
it.
