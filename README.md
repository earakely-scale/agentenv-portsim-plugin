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
environments, at parity with upstream: the same tools, the same tasks and the same reward for the same plan. A live
port is next.

**Contents:** [Parity](#parity-with-portsimenv) · [Run it yourself](#run-it-yourself) · [Tasks](#tasks) ·
[The environment](#the-environment) · [Grading](#grading) · [Built on the AgentEnv Framework](#built-on-the-agentenv-framework) ·
[Layout](#repository-layout) · [Development](#development) · [Licence and credits](#licence-and-credits)

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

What differs is how the env is served, not what the agent sees:

- **Transport.** Upstream serves its tools through OpenEnv, where an episode runs over a WebSocket session. Here an
  AgentEnv env server serves them over MCP (streamable HTTP at `/mcp`), one episode per container.
- **Choosing a task.** Upstream's `reset(task_id=...)` is the extension `urn:portsim:load-task/v1`, which a task
  applies with `apply_server_config`.
- **Reading the grade.** The env grades the plan at submit; the task's verifier reads the reward from `data/get`.
- **Not here:** the 3D viewer, the web UI, the task API and upstream's agent harness. Play and watch episodes in
  upstream's Spaces.

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
`.agentenv/config.toml` to the `modal_vm` profile it describes and run `agent-env portsim setup --platform
linux/amd64`, which pushes the image to the registry the profile names. In an existing agent-env install,
`agent-env plugin add ./agentenv-portsim-plugin` adds the plugin.

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
Tasks that put a model on the 50 eval tasks aren't in the bundle yet.

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
| `data/get` | `task_id`, `checks_used`, `calls_used`, `done`, `end_reason`, `plan`, `grade` and `reward`; never the task's reference |

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
| [Tasks](https://www.agentenvframework.com/docs/tasks/creating) and verifiers | `src/agentenv_portsim/bundles/portsim/`: the tasks and `portsim-verifier`, run with `agent-env run portsim --task <task>` |
| [Registry](https://www.agentenvframework.com/docs/registry): versioned images, envs and runs | `agent-env portsim setup` builds the image `agentenv-portsim-env` and registers the env `portsim`; every run and grade is stored |

## Repository layout

```
src/agentenv_portsim/   the env (server.py) and the agent-env portsim commands (cli.py)
  bundles/portsim/      the wiring tasks and portsim-verifier
src/berth_core/         PortSimEnv's core: tasks, checker, reward, prompts; copied unchanged (VENDORED.md)
data/                   the dock-v1-eval and dock-v1-train task packs, copied unchanged (CC BY-SA 4.0)
tests/                  env, packaging, replay and golden tests
scripts/                record_goldens.py
Dockerfile              the env image
```

## Development

```bash
uv venv && uv pip install -e '.[dev]'
.venv/bin/pytest                         # sets BERTH_TASKS_DIR itself; calls no model
.venv/bin/ruff check .
docker build -t agentenv-portsim-env .   # the env image, for this machine's platform
BERTH_TASKS_DIR=data/dock-v1-eval:data/dock-v1-train .venv/bin/python -m agentenv_portsim.server   # on :18765
```

CI (`.github/workflows/ci.yml`) lints, runs the tests on Python 3.11 and 3.12 and `agent-env plugin check`, then
builds the image and runs the three wiring tasks. Contributions are welcome; [CONTRIBUTING.md](CONTRIBUTING.md)
covers how a change gets in and what must not change.

## Licence and credits

The code is licensed under the Apache License 2.0 ([LICENSE](LICENSE), [NOTICE](NOTICE)); the data is CC BY-SA 4.0.
The wheel and the env image carry both, so the package's licence is `Apache-2.0 AND CC-BY-SA-4.0`.

- **[PortSimEnv v1](https://github.com/adithya-s-k/FineEnvs/tree/b0f4c2f9526e3c45d608b4f92f6ec6c71fecc152/07-simulation-environments/portsim-v1)**
  is by Adithya S Kolavi, part of [FineEnvs](https://github.com/adithya-s-k/FineEnvs), under the Apache License
  2.0. `src/berth_core/` is copied from it unchanged at commit `b0f4c2f` ([VENDORED.md](VENDORED.md)), and the env's
  tools are ported from its OpenEnv server.
- **The task packs** in `data/` were built by Adithya S Kolavi from the Port of Barcelona's 2024 container calls and
  are licensed under CC BY-SA 4.0 ([data/LICENSE](data/LICENSE)). Contains data from the Port de Barcelona open data
  portal. `tests/golden/` and the plans in the bundle's tasks are derived from them, under the same licence.
- **The published episodes** the replay tests read come from the
  [PortSimEnv dataset](https://huggingface.co/datasets/FineEnvs/PortSimEnv) (CC BY-SA 4.0), fetched at a pinned
  revision and never stored here.
- **[AgentEnv Framework](https://www.agentenvframework.com)**
  ([scaleapi/agentenv-framework](https://github.com/scaleapi/agentenv-framework)) runs the tasks and the registry this
  plugin plugs into.

This plugin is independent: neither the Port de Barcelona nor PortSimEnv's author is affiliated with it or endorses
it.
