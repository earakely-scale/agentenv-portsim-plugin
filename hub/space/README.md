---
title: PortSimEnv on AgentEnv
emoji: 🚢
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
base_path: /viewer/
pinned: true
license: other
license_name: cc-by-sa-4.0-cc-by-4.0-meteocat-apache-2.0
license_link: https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/data/LICENSE
short_description: Port of Barcelona weeks on AgentEnv, replayed in 3D
thumbnail: https://huggingface.co/spaces/earakely-scale/PortSimEnv-AgentEnv/resolve/main/thumbnail.jpg
tags:
- agentenv
- rl-environment
- simulation
- logistics
- scheduling
- agents
- weather
- forecasting
- multi-agent
datasets:
- earakely-scale/PortSimEnv-AgentEnv
---

# PortSimEnv on AgentEnv

An agent runs one container quay at the Port of Barcelona for a week of 2024 that has just gone wrong, and decides
when, where and with how many cranes every ship docks. This Space replays the recorded runs on the [AgentEnv
Framework](https://www.agentenvframework.com), on a 3D twin of the quay: twelve models on every lines, wind, marine
and live week, once each, and GPT-6.1 Sol and Claude Sonnet 5.5 on ten v1 weeks. The twelve are Claude Opus, Sonnet
and Haiku 5.5; GPT-6 Astra, GPT-6.1 Sol and GPT-6 Luna; Kimi K3, GLM-5.3, GLM-5.3-Flash, Qwen3.8-2.4T and DeepSeek
V4.1 Flash on Fireworks; and Qwen3.8-27B on Groq.

- **v5, the lines port:** the wind week with the shipping lines answering back. Each ship's agent, the firm the
  port's 2024 record names for its call, is its own A2A agent, which the planner messages: the agents report ETAs that
  firm up as their ships near, and a ship agrees a requested arrival time when it can make it by slowing down. Ships
  berth first come, first served, a ship slowed on request keeping its turn, and an hour at anchor costs what an hour
  late does. As in v4, the week is graded against the lower of the hindsight optimum, which knows every arrival, and
  the best cost of a re-planner that follows the agents' ETAs and asks for arrival times.
- **v4, the wind port:** the marine week in real Barcelona wind. Each week is moved into a real weather week of 2023
  to 2025, and the wind that blew at Meteocat's XEMA station Y7 (Bocana Sud), standing in for the Dique Sur
  anemometer of the port's traffic ordinance, sets its no-movement windows: above 25 kn ships of 300 m or more may not
  berth or leave and every movement takes one more tug; above 30 kn no ship moves. At every watch a Barcelona Port
  Control bulletin, standing in for the port's own forecasts, gives the latest ECMWF forecast published by then,
  adjusted to Y7; the agent plans on the forecasts as they were issued, and the week is graded on the wind that blew.
  A wind run replays with the forecast in force in the watch panel, over a strip of its knots and windows, and the 3D
  quay shows the wind that blew at that hour.
- **v3, the marine port:** the live week with the port's pilots and tugs. Every berthing and departure takes a pilot
  and tugs from pools shared with the rest of the port's real 2024 traffic, and the tug company and the pilot station
  announce cuts. A marine run replays with a pilots-and-tugs line in the watch panel.
- **v2, the live port:** the week as it unfolds. AgentEnv's virtual clock runs it watch by watch, the ships, the
  harbour master, terminal ops and the line desk send their news through triggers, and the agent confirms berths
  under a 6-hour freeze. A live run replays watch by watch: the bulletins as they arrived, the freeze line and each
  window as it froze.
- **v1, a week planned in one go:** the agent checks drafts and submits one plan, graded against a plan CP-SAT proved
  optimal, as in PortSimEnv itself.

The overview's "Start here" opens on GPT-6 Astra's run of
[`dock-36A-w05x1-busy-0-e09`](https://earakely-scale-portsimenv-agentenv.hf.space/viewer/#/run/lines-astra/openai%2Fgpt-6-astra/dock-36A-w05x1-busy-0-e09),
a busy week at Terminal Catalunya (BEST) in the storm week of 11 November 2024 (reward 1.0), the one filmed for the
plugin's README ([full film](https://github.com/earakely-scale/agentenv-portsim-plugin/releases/tag/replays-2026-10-11)).
Astra agrees an arrival hour for every one of the 27 ships with their 7 shipping agents, 11 of the agreements slowing a
ship down, and no ship waits at anchor; each message and its replies are steps of the replay. Then comes the model
board, one table per version, v5 first; click a model to list its weeks, and a week to replay it. The same board is
the dataset's `results` table.

The dataset [earakely-scale/PortSimEnv-AgentEnv](https://huggingface.co/datasets/earakely-scale/PortSimEnv-AgentEnv)
holds the weeks, the references, the runs and their transcripts in two kinds of tables: PortSim's own, one family per
version (`v5_tasks`, `v5_episodes`, `v5_references`, …), and agentenv-hf's standard tables, one pair per bundle, beside
the bundles as agent-env tasks. The environment is the plugin
[earakely-scale/agentenv-portsim-plugin](https://github.com/earakely-scale/agentenv-portsim-plugin), built on
[PortSimEnv](https://github.com/adithya-s-k/FineEnvs/tree/main/07-simulation-environments/portsim-v1), Adithya S
Kolavi's environment in FineEnvs; this viewer is PortSimEnv's.

| | PortSimEnv in FineEnvs | PortSimEnv on AgentEnv |
|---|---|---|
| Environment and code | [FineEnvs/PortSimEnv](https://huggingface.co/spaces/FineEnvs/PortSimEnv) (OpenEnv Space), [code](https://github.com/adithya-s-k/FineEnvs/tree/main/07-simulation-environments/portsim-v1) | [earakely-scale/agentenv-portsim-plugin](https://github.com/earakely-scale/agentenv-portsim-plugin) |
| Eval | [FineEnvs/PortSimEnv-Eval](https://huggingface.co/spaces/FineEnvs/PortSimEnv-Eval) | [the `results` table](https://huggingface.co/datasets/earakely-scale/PortSimEnv-AgentEnv#results), [model board](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/results/board.md) |
| Dataset | [FineEnvs/PortSimEnv](https://huggingface.co/datasets/FineEnvs/PortSimEnv) | [earakely-scale/PortSimEnv-AgentEnv](https://huggingface.co/datasets/earakely-scale/PortSimEnv-AgentEnv) |
| Replays | | this Space |
| Article | [Simulation RL Environments, part 1](https://huggingface.co/spaces/FineEnvs/simulation-rl-environments) | |
| What's next | [Discussion #36](https://github.com/adithya-s-k/FineEnvs/discussions/36) | |

## Play a week yourself

You need Docker (running, usable without `sudo`, with buildx), [uv](https://docs.astral.sh/uv/) and git, and a Hugging
Face token that can make calls to Inference Providers on an account with credits. The plugin comes with
[agentenv-hf](https://github.com/earakely-scale/agentenv-hf-plugin), so `agent-env hf run` plays a week straight from
the dataset:

```bash
uv tool install agentenv-framework \
    --with "agentenv-portsim @ git+https://github.com/earakely-scale/agentenv-portsim-plugin@v0.5.2"
agent-env portsim setup --agent        # build the env and agent images and register them (a few minutes)
agent-env run portsim --task smoke     # no model: grades a known optimal plan, prints "passed"

export HF_TOKEN=hf_...                  # with "Make calls to Inference Providers", on an account with credits
export LITELLM_BASE_URL=https://router.huggingface.co/v1 LITELLM_API_KEY=$HF_TOKEN
agent-env hf run earakely-scale/PortSimEnv-AgentEnv@v0.5.2 --task dock-36A-w06x1-standard-0-e07 \
    --model zai-org/GLM-5.3-Flash:baseten          # the default bundle: dock-v1-eval-lines (v5)
```

`agent-env hf run` downloads the card and the bundles at that tag, checks that the plugins the card names are
installed, shows what it will run and asks first (`--yes` skips the question). `dock-36A-w06x1-standard-0-e07` is the
shortest lines and wind week, 4 watches, and each task stops an episode before it could spend $5. To replay your own
runs on the same viewer, locally, play them as a sweep:

```bash
agent-env portsim sweep run --lines --name mine --models zai-org/GLM-5.3-Flash:baseten \
    --tasks dock-36A-w06x1-standard-0-e07 --episode-cap-usd 1 --cap-usd 3
agent-env portsim view mine            # at http://127.0.0.1:8237/viewer/
```

The [dataset card](https://huggingface.co/datasets/earakely-scale/PortSimEnv-AgentEnv#play-a-week-yourself) has more:
the v4, v3, v2 and v1 bundles and the other open models. If a step fails, see the plugin README's
[troubleshooting](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/README.md#run-it-yourself).

## How this Space runs

`start.sh` downloads the recorded sweeps (`runs/`) from the dataset at its `v0.5.2` tag (`--revision v0.5.2`), and
`agent-env portsim view`, installed from the plugin's `v0.5.2` tag, serves them, replaying each v2 to v5 run
through its week from the recorded tool calls. The 3D twin is downloaded from PortSimEnv's public bucket at start.

## Licence and attribution

- **Tasks and transcripts:** CC BY-SA 4.0, except the weather of v4 and v5 (below). They carry PortSimEnv's dock-v1
  task text, which Adithya S Kolavi built from the Port of Barcelona's 2024 container calls; the other traffic in v3 to
  v5, and v5's ships' agents, are derived from `Barcelona_2024.csv` in
  [alberto-santini/berth-allocation-problems](https://github.com/alberto-santini/berth-allocation-problems) (CC BY-SA
  4.0). Contains data from the [Port de Barcelona open data portal](https://opendata.portdebarcelona.cat/).
- **v5's distances between ports** come from NGA Pub. 151, *Distances Between Ports* (11th edition, 2001), a work of
  the United States government on which no copyright is claimed.
- **The forecasts of v4 and v5**, in their tasks, transcripts and replays, are modified ECMWF open data. Copyright:
  © 2023-2026 European Centre for Medium-Range Weather Forecasts (ECMWF). Source: [www.ecmwf.int](https://www.ecmwf.int).
  Licence Statement: This data is published under a Creative Commons Attribution 4.0 International
  ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)). Disclaimer: ECMWF does not accept any liability
  whatsoever for any error or omission in the data, their availability, or for any loss or damage arising from their
  use. This data is based on data and products of the European Centre for Medium-Range Weather Forecasts (ECMWF).
  Modified: each run's 10 m wind at one grid point, every 3 hours to 72 hours, mapped to the Y7 anemometer by
  quantiles and rounded to whole knots. [Terms of use](https://apps.ecmwf.int/datasets/licences/general/).
- **The observed wind windows of v4 and v5**, in their tasks and replays, are derived from the readings of the Servei
  Meteorològic de Catalunya's (Meteocat) XEMA station Y7, Port de Barcelona – Bocana Sud, in the Generalitat de
  Catalunya's [open data portal](https://analisi.transparenciacatalunya.cat/d/nzvn-apee) (dataset nzvn-apee); no
  reading is included, and they keep the terms published there
  ([Meteocat's legal notice](https://www.meteo.cat/wpweb/avis-legal/)).
  Font: Servei Meteorològic de Catalunya (Meteocat), estació XEMA Y7; dades extretes el 2026-10-08; finestres derivades.
- **The 3D twin:** © OpenStreetMap contributors (ODbL) · terrain: Terrain Tiles (AWS).
- **Code:** the plugin and PortSimEnv's viewer are under the Apache License 2.0.

The plugin's [NOTICE](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/NOTICE) and
[data/LICENSE](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/data/LICENSE) set out each part.
This Space is independent: neither the Port de Barcelona, PortSimEnv's author, ECMWF, Meteocat, the NGA nor any
shipping line or agent named in it is affiliated with it or endorses it.
