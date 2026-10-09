# Contributing

Thanks for helping. Fixes, tasks, tests, docs and bug reports are all welcome.

## How a change gets in

1. **Talk first about anything large.** Open an issue for a new task, extension or change to how the env runs
   before you write it, so we agree on the shape. Small fixes can go straight to a pull request.
2. **Fork, branch and open a pull request against `main`.** Fill in the template: what changes, why, and how you
   tested it.
3. **CI must pass:** lint, the tests on Python 3.11 and 3.12, `agent-env plugin check`, and the image job: it builds
   the env and agent images, runs the three wiring tasks, dry-runs the 50 eval tasks, and runs the golden, replay and
   harness tests against the env image.
4. **The maintainer reviews and approves every pull request.** `main` is protected: a pull request merges only
   with an approving review from the code owner ([.github/CODEOWNERS](.github/CODEOWNERS)), green checks and its
   conversations resolved. Pull requests are squash-merged, so the title becomes the commit message.

First-time contributors' CI runs wait for the maintainer's approval, as GitHub does for public repositories.

## Setup

You need git, [uv](https://docs.astral.sh/uv/) and, for the image, Docker with buildx.

```bash
git clone https://github.com/<you>/agentenv-portsim-plugin && cd agentenv-portsim-plugin
uv venv && uv pip install -e '.[dev]'
.venv/bin/pytest && .venv/bin/ruff check .
```

To try a change end to end, install the checkout into the `agent-env` tool and run the wiring tasks:

```bash
uv tool install agentenv-framework --with-editable .
agent-env portsim setup
agent-env run portsim --task smoke --task wiring-infeasible --task wiring-nosubmit
```

For a change to `portsim-llm`, the eval tasks or the sweep, `setup --agent` builds the agent too, and
`scripts/replay_episode.py` plays a published episode through `agent-env run` with a stand-in model server, at no model
spend (README, [Development](README.md#development)). For a change to the live port,
`agent-env run portsim-live --task wiring-noplay` runs a live week through the gateway without a model, and
`scripts/live_e2e.py` plays one with `portsim-llm` against the stand-in model server (README,
[The live port](README.md#the-live-port)). For the marine port, run the same on `portsim-marine`:
`agent-env run portsim-marine --task wiring-noplay`, and `scripts/live_e2e.py --env portsim-marine --policy rolling`
(README, [The marine port](README.md#the-marine-port)), and for the wind port on `portsim-wind`:
`agent-env run portsim-wind --task wiring-noplay`, and `scripts/live_e2e.py --env portsim-wind --policy rolling`
(README, [The wind port](README.md#the-wind-port)). CI doesn't run any of these yet.

## Where things go

| Change | Code | Tests and docs |
|---|---|---|
| The v1 env, `portsim`: its tools, extensions or data plane | `src/agentenv_portsim/server.py` | `tests/env/`; the README's tool table |
| A task | `src/agentenv_portsim/bundles/portsim/tasks/` | `tests/packaging/`; the bundle's README and the README's task table |
| The verifier | `src/agentenv_portsim/bundles/portsim/artifacts/portsim-verifier/verify.py` | `tests/packaging/` |
| `agent-env portsim setup` | `src/agentenv_portsim/cli.py` | `tests/packaging/` |
| The env image | `Dockerfile` | the CI `image` job |
| The `portsim-llm` agent and its image | `agents/portsim-llm/` | `tests/agent/`, `tests/replay/test_harness.py`; the README's [Play a model](README.md#play-a-model) |
| The eval tasks | `src/agentenv_portsim/tasks.py` | `tests/packaging/test_tasks.py`, `tests/replay/test_prompts.py` |
| The sweep and its report | `src/agentenv_portsim/sweep.py` | `tests/sweep/` |
| The live env, `portsim-live`: its tools, extensions and data plane, the week as known, the freeze, excuses, audit and grade, the reveal schedule | `src/agentenv_portsim/live.py`, `world.py`, `schedule.py` | `tests/live/env/`; the README's [The live port](README.md#the-live-port) |
| A live task, the live verifier, the live sweep | `src/agentenv_portsim/tasks.py`, `bundles/portsim-live/`, `sweep.py` | `tests/live/tasks/` |
| The live references | `scripts/live_references.py`, which writes `data/live/references.jsonl` | `tests/live/tasks/test_live_references.py` |
| The marine env, `portsim-marine`: the pilots and tugs, the other traffic, the marine checker and the situation's pilots and tugs | `src/agentenv_portsim/marine.py`, `PortSimMarineEnv` in `live.py`; its hooks in `world.py` and `schedule.py` | `tests/marine/test_marine_model.py`, `test_marine_world.py`, `tests/live/env/test_marine_env.py`; the README's [The marine port](README.md#the-marine-port) |
| A marine task, the marine sweep | `src/agentenv_portsim/tasks.py`, `bundles/portsim-marine/`, `sweep.py` | `tests/live/tasks/test_marine_tasks.py`, `test_marine_sweep.py` |
| The marine pack and references | `scripts/marine_references.py`, which writes `data/dock-v1-marine/` and `data/marine/references.jsonl` | `tests/marine/test_marine_pack.py`, `test_marine_references.py` |
| The wind env, `portsim-wind`: the wind week, its forecast notices and watches, the week as known, the excuse and the situation's wind | `src/agentenv_portsim/wind.py`, `PortSimWindEnv` in `live.py`; `Week.notice_excuse` in `world.py`, the forecast's lead and speaker in `schedule.py` | `tests/wind/test_wind_world.py`, `test_wind_excuse.py`, `tests/live/env/test_wind_env.py`; the README's [The wind port](README.md#the-wind-port) |
| A wind task, the wind sweep | `src/agentenv_portsim/tasks.py`, `bundles/portsim-wind/`, `sweep.py` | `tests/live/tasks/test_wind_tasks.py`, `test_wind_sweep.py` |
| The weather weeks, the wind pack and references | `scripts/wind_weather.py`, which writes `data/wind/weather.jsonl` and `weather-sources.json`; `scripts/wind_references.py`, which writes `data/dock-v1-wind/` and `data/wind/references.jsonl` | `tests/wind/test_wind_weather.py`, `test_wind_references.py`, on the committed data and the synthetic fixtures in `tests/wind/fixtures/` (`python tests/wind/synthetic.py` rewrites their weather) |
| `portsim-llm`'s live mode | `agents/portsim-llm/agent.py` | `tests/agent/test_agent_live.py`; v1's requests must stay as `tests/golden/harness.json` has them |
| Watching runs: `agent-env portsim view` and `record`, the live week's panel and chart marks, the twin download | `src/agentenv_portsim/episodes.py`, `view.py`, `record.py`, `twin.py`, `web/ext/` | `tests/viewer/`, with the synthetic marine and wind runs in `tests/viewer/marine_runs/` and `wind_runs/` (`python tests/viewer/recorded.py` rebuilds them); the README's [Watch a run](README.md#watch-a-run) |
| PortSimEnv's core, viewer, task packs or published results | never here: `berth_core` is a dependency pinned to a FineEnvs commit, and `src/agentenv_portsim/web/upstream/`, `data/dock-v1-eval/`, `data/dock-v1-train/` and `data/published/` are copied unchanged from upstream ([VENDORED.md](VENDORED.md)) | a new upstream commit is vendored whole, the berth-core pin moves with it, and VENDORED.md names it |

## Conventions

- **Parity comes first.** The tools' names, descriptions, input schemas, output and error text and limits match
  PortSimEnv's exactly, and the replay and golden tests hold them to it, so a change to what an agent sees isn't
  taken here. The same goes for `portsim-llm`: its prompts, nudges, limits and requests match upstream's harness, and
  `tests/golden/harness.json` holds them to it. The live port is this repository's own and has no upstream to match;
  `tests/live/` holds its tools, prompts, schedule and grade instead.
- **Vendored files stay unchanged.** `src/agentenv_portsim/web/upstream/`, `data/dock-v1-eval/`,
  `data/dock-v1-train/` and `data/published/` match upstream byte for byte; the task packs'
  sha256 is checked when they load, and `tests/viewer/test_vendored.py` checks the viewer's. A change to the viewer
  goes in `web/ext/`, through its index.html's import map. The viewer's 3D twin is OpenStreetMap data (ODbL): it is
  never committed, and anything rendered from it carries the attribution.
  `data/live/references.jsonl` is computed here: rerun `uv run --with ortools==9.15.6755 python
  scripts/live_references.py` when the live week, its schedule or its grade changes, and commit the file.
  `data/dock-v1-marine/` and `data/marine/references.jsonl` are computed here too: rerun `uv run --with
  ortools==9.15.6755 python scripts/marine_references.py` when the marine rules or the live week change, and commit
  both. It reads the port's 2024 calls of every ship type at a pinned commit, checked by sha256 and cached under
  `~/.cache/agentenv-portsim/raw/`; that file is never committed. `ortools` is never a dependency; the tests replay
  the files without it.
- **The wind data is rebuilt end to end in seven steps,** each rerun with the ones after it when its input changes;
  commit `data/wind/` and `data/dock-v1-wind/` together:
  1. `uv run --with eccodes==2.49.0 python scripts/wind_weather.py fetch` downloads Meteocat's Y7 readings from the
     Generalitat's open data portal and the ECMWF messages the weeks and the calibration read, by HTTP range, into
     `~/.cache/agentenv-portsim/wind/` (`$XDG_CACHE_HOME/agentenv-portsim/wind/` if that is set; `--cache` for
     another). That is about 85 GB downloaded, of which it keeps each message's point value, sha256 and
     Last-Modified, never GRIB. It took about 50 minutes here; a rerun fetches only what is missing.
  2. `... wind_weather.py fetch --y7-pass 2` fetches the readings again into a second pass, which `build` requires to
     match the first month by month. The cache then holds about 80 MB.
  3. `... wind_weather.py build` writes `data/wind/weather.jsonl` and `weather-sources.json` from the cache alone,
     with no network. The quantile maps are fitted from the cache at each build and never written out.
  4. `uv run --with ortools==9.15.6755 python scripts/wind_references.py screen` plays the 240 pairs of marine and
     weather weeks into `build/wind/screen.jsonl`, about 72 minutes on 14 cores; a restart skips the pairs done.
  5. `... wind_references.py deal` picks the pairs into `build/wind/deal.json`, and fails below 12.
  6. `... wind_references.py pack` writes `data/dock-v1-wind/` from the screen and the deal, without solving.
  7. `... wind_references.py references` replays the stored plans on the pack, checks them against the screen and
     writes `data/wind/references.jsonl`.

  `build/` stays out of git. Never commit a Y7 reading, a quantile map or GRIB: the committed weather is the windows,
  their unvalidated shares, the calibrated whole knots and the pins.
- **The answer key stays in the image.** No tool, extension, route or `data/get` field of any env returns a task's
  reference plans; `portsim`'s grade in `data/get`, there only after a submit, includes the optimal and naive costs,
  and the grade of `portsim-live`, `portsim-marine` and `portsim-wind`, there only once the week ends, the optimal
  cost.
- **Code:** match the code around it. `ruff check .` must pass. Name things so the code reads without comments;
  write a short docstring only for why something is the way it is.
- **Tests:** a fix comes with a test that fails without it. Tests set `BERTH_TASKS_DIR` themselves. They call no
  model: `tests/fake_litellm.py` stands in for the model endpoint. Tests marked `network` or `browser` (the twin
  download, a film with Chrome and ffmpeg) are skipped by default; run them with `pytest -m 'network or browser'`.
- **No secrets or private endpoints** in code, tests, docs or task files: model keys come from agent-env's secret
  store, and examples use placeholders such as `https://your-litellm-proxy`.
- **Licensing:** code contributions are licensed under the Apache License 2.0, like the rest of the code. Anything
  derived from the task packs or the port's 2024 calls (plans, situations, the marine pack's other traffic, recorded
  outputs) is CC BY-SA 4.0 and must be listed in [NOTICE](NOTICE). Recorded episodes from the published dataset are fetched by the tests, never committed.
  The wind data's weather keeps its sources' terms, and anything that shows it carries their attribution: ECMWF's
  wording for the forecasts and Meteocat's source line for the observed windows ([NOTICE](NOTICE),
  [data/LICENSE](data/LICENSE)).

## Reporting bugs and security issues

Open an issue with the task or command, the PortSim task id, what you expected, what happened, and the run's instance
id or log. For a security issue, use GitHub's private vulnerability reporting instead ([SECURITY.md](SECURITY.md)).
