---
license: other
license_name: cc-by-sa-4.0-cc-by-4.0-meteocat-apache-2.0
license_link: https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.4.3/data/LICENSE
pretty_name: PortSimEnv on AgentEnv
language:
- en
task_categories:
- reinforcement-learning
- text-generation
size_categories:
- n<1K
tags:
- agentenv
- rl-environment
- agents
- simulation
- logistics
- scheduling
- operations-research
- mcp
- real-world-data
- weather
- forecasting
configs:
- config_name: v4_tasks
  default: true
  data_files:
  - split: eval
    path: tasks/v4.parquet
- config_name: results
  data_files:
  - split: eval
    path: results/board.parquet
- config_name: v4_episodes
  data_files:
  - split: eval
    path: episodes/v4.parquet
- config_name: v4_references
  data_files:
  - split: eval
    path: references/wind.parquet
- config_name: v3_tasks
  data_files:
  - split: eval
    path: tasks/v3.parquet
- config_name: v3_episodes
  data_files:
  - split: eval
    path: episodes/v3.parquet
- config_name: v3_references
  data_files:
  - split: eval
    path: references/marine.parquet
- config_name: v2_tasks
  data_files:
  - split: eval
    path: tasks/v2.parquet
- config_name: v2_episodes
  data_files:
  - split: eval
    path: episodes/v2.parquet
- config_name: v2_references
  data_files:
  - split: eval
    path: references/live.parquet
- config_name: v1_tasks
  data_files:
  - split: eval
    path: tasks/v1.parquet
- config_name: v1_episodes
  data_files:
  - split: eval
    path: episodes/v1.parquet
agentenv:
  default: dock-v1-eval-wind
---

# PortSimEnv on AgentEnv

[![GPT-6.1 Sol plays a wind week at the Port of Barcelona: at each watch Barcelona Port Control's forecast arrives as a bulletin, the watch panel draws its knots and windows, and the storm that blew raises whitecaps and a no-movement banner on the quay](https://raw.githubusercontent.com/earakely-scale/agentenv-portsim-plugin/v0.4.3/assets/wind-port.webp)](https://earakely-scale-portsimenv-agentenv.hf.space/viewer/#/run/wind-pilot-gpt/openai%2Fgpt-6.1-sol/dock-24B-w37x1-standard-0-e01)

<sub>GPT-6.1 Sol plays the wind week `dock-24B-w37x1-standard-0-e01`, APM Terminals Barcelona's schedule in the wind of
the week of 6 March 2023; the film's clock shows the schedule's own 2024 dates. At each watch (see [Terms](#terms)) a
Barcelona Port Control bulletin, standing in for the port's own forecasts, gives the ECMWF run published by then. The
Thursday 18:00 bulletin (issued 15:00) warns of wind above 25 kn in hours 127–130, and the Friday 12:00 one (issued
09:00) in 125–129. The agent berths VIENNA EXPRESS (335 m) at hour 130, after the latest window. The wind blew above
25 kn from 122 to 135, and above 30 kn to 125: longer and earlier than any forecast showed, so hour 130 is excused.
The plan is feasible at 301 against the forecast-following re-planner's 252 (reward 0.62); ignoring the forecast is
infeasible (0.187).
**▶ [Watch this week](https://earakely-scale-portsimenv-agentenv.hf.space/viewer/#/run/wind-pilot-gpt/openai%2Fgpt-6.1-sol/dock-24B-w37x1-standard-0-e01)**
on the [replay Space](https://huggingface.co/spaces/earakely-scale/PortSimEnv-AgentEnv), or the
[full film](https://github.com/earakely-scale/agentenv-portsim-plugin/releases/tag/replays-2026-10-09). Twin ©
OpenStreetMap contributors (ODbL); forecasts ECMWF open data (CC BY 4.0, modified); wind windows derived from Meteocat
XEMA Y7.</sub>

An agent runs one container quay at the Port of Barcelona for a week of 2024 that has just gone wrong: late and
bunched ships, closed quay sections, crane breakdowns, gales, emergencies. It decides when, where along the quay and
with how many cranes every ship docks, and the week is graded deterministically, with no judge, against plans the
CP-SAT solver finds. The ships and their calls, the quays' crane fleets and the port's berth and wind rules are real;
the workloads and the disruptions are simulated, except in v4, where the storms and their forecasts are real. This
dataset holds the weeks and the recorded runs of that environment on the
[AgentEnv Framework](https://www.agentenvframework.com), in four versions:

- **v4, the wind port** (env `portsim-wind`): v3's marine week moved into a real Barcelona weather week of 2023 to 2025.
  The wind that blew at Meteocat's station Y7, standing in for the Dique Sur anemometer of the port's traffic
  ordinance, sets the no-movement windows, and at every watch a Barcelona Port Control bulletin, standing in for the
  port's own forecasts, gives the latest ECMWF run published by then, adjusted to Y7. The agent plans on the forecasts
  as they were issued, and the week is graded on the wind that blew.
- **v3, the marine port** (env `portsim-marine`): v2's live week, where every berthing and departure also takes a
  pilot and tugs in its hour, from port-wide pools shared with the rest of the port's real 2024 traffic. The tug
  company and the pilot station announce cuts during the week, and a gale adds a tug to most movements.
- **v2, the live port** (env `portsim-live`): the week played as it unfolds. AgentEnv's virtual clock runs it watch by
  watch, the ships, the harbour master, terminal ops and the line desk send their news through triggers, windows
  about to start are frozen, and the agent confirms berths as it goes. It is graded on what it confirmed, against the
  week as it really happened.
- **v1, a week planned in one go** (env `portsim`): the agent reads the situation, checks drafts and submits one
  plan, as in PortSimEnv itself.

Each version's weeks are also a bundle of agent-env tasks, published with
[agentenv-hf](https://github.com/earakely-scale/agentenv-hf-plugin) beside PortSim's own tables, so
`agent-env hf run` plays a week straight from this dataset ([Play a week yourself](#play-a-week-yourself)).

The environment is the plugin
[earakely-scale/agentenv-portsim-plugin](https://github.com/earakely-scale/agentenv-portsim-plugin), built on
[PortSimEnv](https://github.com/adithya-s-k/FineEnvs/tree/main/07-simulation-environments/portsim-v1), Adithya S
Kolavi's environment in [FineEnvs](https://github.com/adithya-s-k/FineEnvs). Its own tasks, including the 1,050
training weeks, and rollouts are in [FineEnvs/PortSimEnv](https://huggingface.co/datasets/FineEnvs/PortSimEnv). See
also the collection
[PortSimEnv on AgentEnv](https://huggingface.co/collections/earakely-scale/portsimenv-on-agentenv-6ac6e1fc8313fc0cb74a54f1).

## Tables

Two kinds of tables, all parquet, all under the split `eval` (for the words they use, see [Terms](#terms)). PortSim's
own, one family per version:

| Config | Split | Rows | What |
|---|---|---:|---|
| `v4_tasks` (default) | `eval` | 15 | the wind weeks: what the agent is told at the start, each watch's news with Port Control's forecast, the wind that blew, and the reference costs |
| `results` | `eval` | 38 | the model board: one row per version and model, with its mean reward over the weeks and its 95% CI, each tier's mean, and how many weeks it finished, kept feasible and played to the optimum (v4: the anchor), with its tokens, cost and time ([Results](#results)) |
| `v4_episodes` | `eval` | 180 | twelve models on the wind weeks, once each: the grade, the tool calls and the full transcript |
| `v4_references` | `eval` | 15 | for each wind week, the hindsight optimum, the forecast-following and forecast-blind re-planners and the naive policy, and the conditions it qualified on |
| `v3_tasks` | `eval` | 15 | the marine weeks: what the agent is told at the start, including the pilots and tugs free each hour, each watch's news, and the reference costs |
| `v3_episodes` | `eval` | 180 | the twelve models on the marine weeks |
| `v3_references` | `eval` | 18 | for each one-week eval week, a rolling CP-SAT re-planner and a naive policy played with pilots and tugs, and whether it qualifies |
| `v2_tasks` | `eval` | 15 | the live weeks, the same 15 without pilots and tugs |
| `v2_episodes` | `eval` | 180 | the twelve models on the live weeks |
| `v2_references` | `eval` | 18 | for each of the 18 one-week eval weeks, the rolling re-planner and the naive policy, and whether it qualifies (15 do: the live weeks) |
| `v1_tasks` | `eval` | 50 | the eval weeks planned in one go: the prompts, the optimal and naive plans |
| `v1_episodes` | `eval` | 20 | GPT-6.1 Sol and Claude Sonnet 5.5 on ten of those weeks |

And agentenv-hf's, one pair per bundle, exactly as `agent-env hf publish` writes them:

| Config | Split | Rows | Bundle | Version |
|---|---|---:|---|---|
| `dock-v1-eval-wind_tasks`, `dock-v1-eval-wind_episodes` | `eval` | 15, 180 | `bundles/dock-v1-eval-wind` | v4 |
| `dock-v1-eval-marine_tasks`, `dock-v1-eval-marine_episodes` | `eval` | 15, 180 | `bundles/dock-v1-eval-marine` | v3 |
| `dock-v1-eval-live_tasks`, `dock-v1-eval-live_episodes` | `eval` | 15, 180 | `bundles/dock-v1-eval-live` | v2 |
| `dock-v1-eval_tasks`, `dock-v1-eval_episodes` | `eval` | 50, 20 | `bundles/dock-v1-eval` | v1 |

A bundle's `_tasks` table has one row per task of the bundle, with its prompt, envs, verifiers and steps; its
`_episodes` table has one row per recorded run, with its status, model, reward, the verifier's full output and the
transcript as chat messages. They hold the same runs as PortSim's episode tables, with the same rewards: `episode_id`,
e.g. `dock-v1-eval-wind/dock-24B-w06x1-busy-0-e15-iamceybb`, joins `v4_episodes` to `dock-v1-eval-wind_episodes` and
to the line of `raw/dock-v1-eval-wind.jsonl` with that id, and so for each version. A PortSim table's `task_id` is an
agentenv-hf table's `task` (agentenv-hf's own `task_id` is `<bundle>/<task>`).

Every week is an eval week. The 15 live weeks are the one-week eval weeks on which the rolling re-planner reaches
the hindsight optimum, so a perfect score is reachable on what the agent could know; with pilots and tugs, the same
15 qualify. A wind week pairs a marine week with a weather week. Of the 240 pairs of the 15 marine weeks and 16
weather weeks (14 storm weeks and 2 false alarms), 26 qualify, those that meet four conditions: (a) the
forecast-following re-planner costs no more than the hindsight optimum and (b) ignoring the forecast (in a false-alarm
week, holding every warning) scores 0.9 or less, each in at least 3 of its 4 solver configurations; (c) the week has
at most 10 watches; (d) no ship alongside at hour 0 is due to leave inside a window above 30 kn. 15 are dealt: 14 wind
weeks set in 9 of the 14 storm weeks (2025-W03, `e12`, in four of them), the storm wind weeks, and one in 2023-W44's
false alarm, on `dock-24B-w07x1-busy-0`. They use 11 of the marine weeks' schedules, three of them more than once.

A task id reads `dock-<quay>-w<week>x<weeks>-<difficulty>-<seed>`: `dock-24B-w07x1-busy-0` is week 7 of 2024 at quay
24B, one week long, busy tier. A wind week adds its weather week, `-e00` to `-e15`: `dock-24B-w37x1-standard-0-e01` is
the marine week `dock-24B-w37x1-standard-0` in the wind of 2023-W10. A v1 task can span up to three weeks (`x2`,
`x3`); a v2, v3 or v4 week is always one. `dock-v1` is the name of PortSimEnv's task pack, which all four versions
use, not this dataset's version.

## Terms

- **Week**: one task, a quay with its ships and what goes wrong. **Watch** (v2 to v4): watch 0 opens the week at
  hour 0, and a new watch starts at each news bulletin; the agent re-plans each watch, and a window starting within 6
  hours (the freeze) can no longer change. A wind week has 4 to 10 watches and always 52 turns, those of 10 watches,
  so the turns don't give the count away; v2 and v3 weeks have 47. **Validity audit** (v2 to v4): the env's check that
  every bulletin arrived once, on time, at its watch; a run that fails it is not scored.
- **Pilots and tugs** (v3, v4): a pilot is the local mariner who boards to guide a ship in or out of the port, and
  tugs are the boats that push and pull it alongside. Every berthing and departure of a ship of 45 m or more takes a
  pilot, and tugs by length (0 under 120 m, up to 3 from 300 m), in its hour, from 7 pilots and 8 tugs on duty; inside
  an announced gale window (in v4, in wind above 25 kn) most movements take one more tug (not Ro-Ro ships and ferries
  under 200 m, nor yachts).
  The port's other 2024 calls use the same pools. In any hour the quay's ships may need no more than are free; a
  short hour is a rule break.
- **Wind rules** (v4): above 25 kn (10-minute mean), ships of 300 m or more may not berth or leave and every movement
  takes one more tug, with the exemptions above; above 30 kn no ship moves (the port's traffic ordinance,
  BOE-A-2023-6719). The wind is read at Meteocat's XEMA station Y7, which stands in for the ordinance's Dique Sur
  anemometer, and the hours it blew above each threshold are the week's no-movement windows; a range a–b runs from
  hour a up to, not including, hour b. v3's gale is gone; the agent sees only forecasts and the wind observed so far.
- **Forecast bulletin** (v4): at every watch a Barcelona Port Control bulletin, standing in for the port's own
  forecasts, gives the latest ECMWF open-data (HRES) run published by then, adjusted to Y7 by quantile maps fitted on
  another year, in whole knots. A run counts as published 9 hours after it starts. The bulletin gives the hours above 25
  and 30 kn it shows and its peak; the situation adds its knots every 3 hours. A watch is added at 00:00 or 12:00 when
  the run in force then shows an hour above 25 or 30 kn, 6 to 42 hours ahead, that the run at the watch before didn't.
- **Storm week, false-alarm week** (v4): the weather weeks a wind week is set in. A storm week had a window above 25
  kn of 4 hours or more, or an hour above 30 kn, at Y7; a false-alarm week (`bust` in the tables) stayed below that,
  though its forecasts showed hours above 25 kn that didn't blow. The 14 wind weeks set in a storm week are the storm
  wind weeks.
- **Optimum**: the cost of the best plan CP-SAT, a constraint solver, finds for the week as it really happened. A
  **solver configuration** is one of the 4 ways the references run CP-SAT: 1 or 8 workers, each with or without an
  earliest-finish tie-break. **Hindsight** (v4): that optimum with the whole week known, in the wind that blew.
  **Anchor** (v4): the lower of the hindsight optimum and the forecast-following re-planner's best cost over its 4
  solver configurations; v4 scores against it, and it is v4's `optimal_cost`. The agent's cost is net of its excuses
  while hindsight pays for all the wind, so following the forecast can cost less than hindsight; the anchor is below it
  in 5 of the 15 wind weeks.
- **Rolling**: a CP-SAT re-planner that only knows what has been announced; in v4 that includes the forecast, so it
  is the forecast-following re-planner. **Blind** (v4): the same re-planner with the wind taken out of the week as
  known. **Hold** (v4, the false-alarm week): the same, holding every window any forecast so far has shown. **Naive**:
  a simple policy that pushes ships later (in v2 to v4, it keeps each confirmed window that still fits and moves the
  rest; it knows nothing of pilots and tugs, so in v3 it often breaks their rule). **Unavoidable**: the cost no plan
  avoids; in v4, in the wind that blew (the floor). **Regret**: cost above the optimum, in v4 above the anchor.
  **Excused cost**: cost the grade excuses, which is not charged: in v2 and v3, cost that news put on a frozen window;
  in v4, the cost the excuse waives.
- **The excuse** (v4): per ship, at its freeze, on the whole plan. A ship first frozen at watch k is compared with the
  week as known at watch k−1, its news and its forecast, and a rule break or cost the week adds to that is excused,
  once. So wind that no forecast had shown by then is excused, and wind the forecast showed and that blew is charged,
  as an ignored warning. A problem ships share (an overlap, or pilots, tugs or the move limit short at an hour) is
  judged for each of them as the ship decided last saw it.
- **Reward**: 0.2 + 0.8·e^(−gap/0.5) for a valid plan, where gap = max(0, cost − optimum) / (max(0, optimum −
  unavoidable) + 100), so the optimum scores 1.0; in v4 the anchor and the floor take the optimum's and the
  unavoidable cost's places. A plan that breaks a rule scores under 0.2 (0.2 times the share of ships placed
  cleanly), and a run that submits nothing scores 0. The confidence intervals below are bootstrap intervals over
  weeks.
- **Sweep**: one batch of runs (models × weeks), recorded in `runs/`; the sweeps named `…-pilot-…` were small first
  batches of two weeks, unrelated to harbour pilots. **Bundle**: a folder of agent-env tasks; `bundles/` has one per
  version.

## Use

```python
import json
from datasets import load_dataset

repo = "earakely-scale/PortSimEnv-AgentEnv"
weeks = load_dataset(repo, "v4_tasks", split="eval", revision="v0.4.3")
week = weeks[0]
# what the agent gets at hour 0
print(week["system_prompt"], week["situation"], sep="\n\n")
# what arrives later, Port Control's forecast included
for watch in json.loads(week["watches"]):
    print(watch["hour"], [n["text"] for n in watch["notices"]])
# the wind that blew, which the grade reads
print(json.loads(week["wind_windows"]))

episodes = load_dataset(repo, "v4_episodes", split="eval", revision="v0.4.3")
# a list of chat messages: no json.loads
messages = episodes[0]["messages"]
call = next(c for m in messages if m["tool_calls"] for c in m["tool_calls"]
            if c["function"]["name"] == "check_plan")
# the arguments are an object
a = call["function"]["arguments"]
# the plan as sent: a JSON string from Claude Sonnet 5.5, a list from GPT-6.1 Sol
plan = a["plan"] if isinstance(a["plan"], list) else json.loads(a["plan"])
print(plan)
```

`messages`, in every `vN_episodes` table, is now a list of chat messages, the type agentenv-hf writes: OpenAI roles,
`tool_calls` of `{id, type, function: {name, arguments}}` with `arguments` an object, and `tool_call_id` and `name`
on tool messages, which TRL's `SFTTrainer` and transformers chat templates read. In v0.3.x it was a JSON string. The
other columns holding JSON (`watches`, `wind_windows`, `task`, the plans, `steps`, and the references' `rolling_plans`,
`configs`, `solver` and `clauses`) are still strings; `json.loads` them. agentenv-hf's JSON columns (`scores`,
`verifications`, `structured_output` and its tasks' `steps`) come back as Python objects in `datasets` 5.1.

## Play a week yourself

You need Docker (running, usable without `sudo`, with buildx), [uv](https://docs.astral.sh/uv/) and git. Install
the plugin, which brings agentenv-hf with it, build the images, and check it all works with a free task that calls no
model:

```bash
uv tool install agentenv-framework \
    --with "agentenv-portsim @ git+https://github.com/earakely-scale/agentenv-portsim-plugin@v0.4.3"
# build the env and agent images and register them (a few minutes)
agent-env portsim setup --agent
# no model: grades a known optimal plan, prints "passed"
agent-env run portsim --task smoke
```

Then play a week straight from this dataset. You need a Hugging Face token with the "Make calls to Inference
Providers" permission, on an account with credits; each task stops an episode before it could spend $5.

```bash
# with "Make calls to Inference Providers", on an account with credits
export HF_TOKEN=hf_...
export LITELLM_BASE_URL=https://router.huggingface.co/v1 LITELLM_API_KEY=$HF_TOKEN
# the default bundle: dock-v1-eval-wind (v4)
agent-env hf run earakely-scale/PortSimEnv-AgentEnv@v0.4.3 \
    --task dock-36A-w06x1-standard-0-e07 --model zai-org/GLM-5.3-Flash:baseten
# v3; dock-v1-eval-live is v2, dock-v1-eval v1
agent-env hf run earakely-scale/PortSimEnv-AgentEnv@v0.4.3 --bundle dock-v1-eval-marine \
    --task dock-24B-w07x1-busy-0 --model zai-org/GLM-5.3-Flash:baseten
```

`hf run` downloads this card and `bundles/` at the tag's commit into
`~/.cache/agentenv-hf/earakely-scale/PortSimEnv-AgentEnv/<commit>`, checks that the plugins the card's `agentenv`
table names are installed (it never installs them itself), shows what it will run and asks first: `--yes` skips the
question, and `--dry-run` runs nothing. Without `--bundle` it plays the card's default, `dock-v1-eval-wind`.
`dock-36A-w06x1-standard-0-e07` is the shortest wind week, with 4 watches.

The open models priced for the router are `Qwen/Qwen3.8-2.4T-A95B:together`, `Qwen/Qwen3.8-27B:ovhcloud`,
`zai-org/GLM-5.3-Flash:baseten` and `zai-org/GLM-5.3:together`; closed models go through a LiteLLM proxy (the plugin
README's [Play a model](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.4.3/README.md#play-a-model)).
If a step fails, the plugin README's
[troubleshooting](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.4.3/README.md#run-it-yourself)
covers the usual causes (`agent-env` not on the PATH, port 5000 taken by macOS AirPlay).

## Replay and publish your own runs

To replay your own runs on the same viewer as the Space, play them as a sweep, which records each run under
`results/runs/<name>/`, then serve them. `--wind` plays wind weeks, `--marine` and `--live` play v3 and v2, and a
sweep with none of them plays v1.

```bash
agent-env portsim sweep run --wind --name mine --models zai-org/GLM-5.3-Flash:baseten \
    --tasks dock-36A-w06x1-standard-0-e07 --episode-cap-usd 1 --cap-usd 3
# http://127.0.0.1:8237/viewer/
agent-env portsim view mine
```

To publish them as a Hub dataset of your own, give `agent-env hf publish` the sweep's bundle,
`results/runs/<name>/bundle`. Write it to a folder first and look, then push:

```bash
# look first
agent-env hf publish results/runs/mine/bundle --name dock-v1-eval-wind --out mine-dataset
# then push
agent-env hf publish results/runs/mine/bundle --name dock-v1-eval-wind --repo you/portsim-runs
```

It writes the same tables as this dataset's `dock-v1-eval-wind_*` configs, the raw records and the bundle, under the
split `train` unless `--split` names another, and pushes them in one commit; pushing needs a token with write access.
Before writing anything it scans every file for this machine's keys and for token shapes, and stops on a hit.
Transcripts are published as the agent wrote them, so read a run's `messages` before you make a dataset public.
`--requires` and `--setup` write what the bundle needs to the card, as this card's `agentenv` table does, for
`agent-env hf run` to check; [agentenv-hf's README](https://github.com/earakely-scale/agentenv-hf-plugin/blob/v0.3.0/README.md#publish)
lists every option. The plugin README covers sweeps and filming a run.

## Dataset structure

**Tasks** (`v4_tasks`, `v3_tasks`, `v2_tasks`, `v1_tasks`), one row per week:

- `task_id`, `quay`, `terminal`, `difficulty` (standard, busy, storm or extreme), `week`, `week_start_utc`,
  `num_ships`, `num_disruptions`. A wind week keeps its schedule's 2024 week.
- `system_prompt`, `situation`: the rules and the opening message, exactly as the agent receives them. In v3 and v4
  the situation has a "Pilots and tugs" section: the pools, the rule, the tugs each ship takes, and the pilots and
  tugs free for the quay's ships each hour. In v4 a "Wind at the Dique Sur" section follows it: the wind rules, the
  forecast in force, its knots every 3 hours and the wind observed so far.
- `optimal_cost`: the cost of the best plan CP-SAT finds for the week as it really happened; in v4, the anchor.
  `naive_cost`: v1, a plan that pushes ships later; v2 to v4, the naive policy's cost, empty when its plan breaks a
  rule (`naive_feasible`).
- v2 to v4: `num_watches`, `watches` (each watch's hour and its notices: who sends it, the hour it is about, the
  text; in v4 one of them is Barcelona Port Control's forecast), `rolling_cost` (the rolling CP-SAT re-planner) and
  `unavoidable_cost` (what no plan avoids).
- v3 and v4: `pilots` and `tugs` (the pools on duty), `other_movements` (the number of berthings and departures of the
  port's other traffic the pools also serve; the movements themselves are in `task`). v3 only: `v2_optimal_cost` (the
  same week's optimum without pilots and tugs).
- v4 only: `schedule` (the marine week it is built on), `v3_optimal_cost` (that week's optimum in the marine port),
  `hindsight_cost`, `blind_cost` (empty when the blind plan breaks a rule) and `blind_feasible`, `weather_id`
  (`e00` to `e15`), `weather_week` (the ISO week, e.g. `2023-W10`), `weather_monday_utc`, `weather_kind` (`storm` or
  `bust`), and `wind_windows`: the windows that blew, each with its `start` and `end` hour, `above_kn` (25 or 30) and
  `unvalidated`, the share of its Y7 readings not yet validated. The grade reads them; the agent sees only the wind
  observed before each watch.
- v1 only: `proven_optimal`, `optimal_plan`, `naive_plan`. A plan is a list of
  `{"ship": id, "berth_hour": h, "section": s, "cranes": c}`.
- `task`: the full week as the task pack has it, including every disruption (in v3 and v4 the pools and the other
  traffic's movements; in v4 the windows that blew and the forecast in force at each watch); in v2 to v4 the agent
  learns the disruptions only as their notices arrive.

**Episodes** (`v4_episodes`, `v3_episodes`, `v2_episodes`, `v1_episodes`), one row per model and week:

- `episode_id` (the run, as in agentenv-hf's tables), `model`, `model_name`, `task_id`, `difficulty`, `quay`,
  `num_ships`.
- `reward` (0 to 1), `feasible`, `cost` (of the plan, or of the confirmed windows in v2 to v4), `optimal_cost` (in
  v4, the anchor).
- v2 to v4: `num_watches`, `regret` (cost above the optimum, in v4 above the anchor), `excused_cost` (cost excused,
  not charged). v1: `submitted`, `checks`.
- `turns`, `tool_calls`, `input_tokens`, `output_tokens`, `cost_usd` (model spend at prices pinned in October 2026),
  `seconds`, `end_reason`, `sweep` (the run it comes from); v2 to v4 `reached_end` (the agent played to the week's
  end; otherwise the week ran on to its end on the windows confirmed so far).
- `final_plan`: in v1 the plan the model submitted (`null` for the one run that submitted none, below); in v2 to v4
  the confirmed windows, as the verifier graded them. `steps` (each tool call with its plan), `messages` (the full
  transcript, as chat messages).

**Results** (`results`), one row per version and model, best first, from the episode tables: `version`, `env`,
`model`, `model_name`, `provider` (who served it), `weeks`, `runs`, `mean_reward` with its 95% CI (`ci_low`,
`ci_high`: a bootstrap over the weeks, drawn in task id order as the plugin's sweep reports do), `reward_standard`,
`reward_busy` (v1 also `reward_storm`, `reward_extreme`), `finished` (v1: submitted; v2 to v4: reached the week's end),
`feasible`, `optimal` (in v4, at the anchor), `median_turns`, `input_tokens`, `output_tokens`, `cost_usd`,
`cost_per_episode` and `median_seconds`. `results/v4.json` (and `v3.json`, `v2.json`, `v1.json`) hold the same board
in the shape of PortSimEnv's article data (`portsim-results.json`): `model`, `key`, `n`, `mean`, `tiers`, `submitted`,
`feasible`, `optimal`, `tokens_out`, `tokens_in`, `median_s`, plus `ci`, `provider` and `cost_usd`.

**References** (`v4_references`, `v3_references`, `v2_references`). v2 and v3 have one row per one-week eval week:
`qualifies`, `optimal_cost`, `unavoidable_cost`, `watch_hours`, the rolling re-planner's and the naive policy's
`cost`, `reward`, `feasible` and `excused_cost` (`rolling_cost` to `naive_excused_cost`), `rolling_plans` (the rolling
plans per watch), `configs` (each solver configuration's cost; in v4 also its reward) and `solver` (the solver
settings); v3 adds `v2_optimal_cost`. v4 has one row per wind week, with the same columns (`optimal_cost` is the
anchor) and `schedule`, `weather`, `kind`, `hindsight_cost`, `v3_optimal_cost`, `added_watches` (the watches its
forecasts added), the blind re-planner's `blind_cost` to `blind_excused_cost`, and `clauses` (whether the week meets
each of the four conditions above, `a` to `d`); in the false-alarm week, the hold-every-warning re-planner's
`hold_cost` to `hold_excused_cost`, empty in the storm wind weeks.

**agentenv-hf's tables** (`<bundle>_tasks`, `<bundle>_episodes`) are what `agent-env hf publish` writes for any
bundle; [agentenv-hf's README](https://github.com/earakely-scale/agentenv-hf-plugin/blob/v0.3.0/README.md#whats-in-the-dataset)
describes every column. In brief: `_tasks` has `task`, `task_id`, `evals`, `prompt`, `envs`, `agents`, `verifiers`,
`num_steps` and `steps`; `_episodes` has `episode_id`, `task`, `task_version`, `run_group`, `status`, `created_utc`,
`completed_utc`, `model`, `agent`, `reward` and `scores` (the `portsim` verifier's), `prompt` and `response`,
`messages`, `tool_calls` (the count), `trajectory_format`, `failed_step`, `error_type`, `error`, `verifications` and
`structured_output`.

**Files** beside the tables: `bundles/<bundle>/` holds each version's weeks as agent-env tasks (what
`agent-env hf run` plays), `raw/<bundle>.jsonl` each run's record and native trajectory, one run per line,
`references/` the references also as JSONL, `results/` the board as JSON, and `runs/` the raw sweeps the replay
Space reads.

## Results

Twelve models, once each on every live, marine and wind week, with the same harness, prompts, tools and limits: the
mean reward on each version and over all 45 weeks, each week weighing the same. The plugin's
[results/board.md](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.4.3/results/board.md) analyses
them.

<!-- board:all -->

<!-- /board:all -->

**v4, the wind port**, twelve models, one run per model and week. They all play the same harness, `portsim-llm`, with
the same prompts, tools and limits, through Scale's LiteLLM proxy: Claude on Anthropic's API, GPT on the Responses API
(served by Azure OpenAI), the open models on Fireworks, and Qwen3.8-27B on Groq, which takes at most 16,384 output
tokens a reply against 32,000 for the others. On the same weeks the forecast-following re-planner scores 1.000, the
blind one 0.237 and the naive policy 0.183.

<!-- board:v4 -->

<!-- /board:v4 -->

- **Three models lead, within noise of each other:** Claude Opus 5.5 (0.906), GPT-6 Astra (0.896) and Claude Sonnet
  5.5 (0.888). Opus and Sonnet broke no rule in any of the 15 weeks, Astra one (a movement short of tugs), and Astra
  ends 9 of the 15 weeks at the anchor. GPT-6.1 Sol follows at 0.745, with three weeks of its own rule breaks.
- **The best open model is Qwen3.8-2.4T** (0.662), ahead of Claude Haiku 5.5 (0.583): 0.926 on the three standard
  weeks, 0.596 on the busy ones, and feasible in 10 of 15.
- **The other open models break rules in most weeks, and rarely the wind's.** Kimi K3 breaks one in 10 of its 15
  weeks, mostly overlapping berths and more cranes than the quay has; GLM-5.3-Flash in 10; GLM-5.3 and DeepSeek V4.1
  Flash in 8 (DeepSeek stops calling tools with ships still unplanned in 5); Qwen3.8-27B in all 15. A wind window is
  broken in 6 of the 180 runs.
- **GPT-6 Luna's plans are mostly valid but costly:** feasible in 13 weeks, never at the anchor, 0.320.
- **Checking is not the difference; heeding it is.** Every model calls `check_plan` 5 to 13 times a week. How often it
  then confirms windows straight after a check that reported problems: Claude Opus 5.5 2%, Claude Sonnet 5.5 11%,
  Claude Haiku 5.5 12%, Qwen3.8-2.4T 18%, GPT-6 Astra and GLM-5.3 19%, GPT-6 Luna 20%, DeepSeek V4.1 Flash 31%, GPT-6.1
  Sol 55%, GLM-5.3-Flash 57%, Kimi K3 60%, Qwen3.8-27B 94%. Confirming commits only the near windows, so this is a
  habit, not a rule break in itself: GPT-6.1 Sol keeps 12 weeks feasible.
- **The false alarm,** `dock-24B-w07x1-busy-0-e04`: GPT-6 Astra and Qwen3.8-2.4T end at the optimum's 226 (1.000),
  Claude Opus 5.5, Claude Sonnet 5.5 and GPT-6.1 Sol at 227 (0.989), well clear of holding every warning (242, 0.845).
- **18 feasible runs cost less than the hindsight optimum,** as the forecast-following re-planner can: the grade
  excuses wind no forecast showed, while hindsight pays for all of it.
- Every run passed the validity audit. A run that failed (a deploy, a provider error, a cost cap) was played again
  from the start; the plugin's `results/wind.md` counts every attempt and lists the runs left unscored. The ten new
  models' wind weeks recorded $137 of model spend, of which $110 is in the runs shown here; a request whose usage never
  arrived is counted at the most it could have cost.
- The harness gained three fixes for provider failures during these runs: eight retries on chat completions, for
  Groq's tokens-per-minute limit; a reply that fails mid-stream is sent again; and a tool call whose arguments aren't
  JSON goes back into the model's history as `{}`, which Fireworks requires. None changes a run whose requests
  succeed, and no run scored before them sent such a call.

**v3, the marine port**, the same twelve models, one run per model and week. On the same weeks the rolling
re-planner scores 1.000 and the naive policy, which knows nothing of pilots and tugs, 0.187 (infeasible in 9 of the
15 weeks):

<!-- board:v3 -->

<!-- /board:v3 -->

- **GPT-6 Astra (0.956), Claude Opus 5.5 (0.951) and Claude Sonnet 5.5 (0.932) lead again,** and none of them broke a
  rule in any week. GPT-6.1 Sol (0.905) is closer behind than on the wind weeks; its one infeasible week is
  `dock-24B-w35x1-busy-0`, where at its last watch it confirmed windows before checking them and advanced with a
  pilot-short hour in its plan.
- **Claude Haiku 5.5** (0.639) keeps all 15 weeks feasible but plays none to the optimum.
- **The open models break a rule in 5 (GLM-5.3) to 15 (Qwen3.8-27B) of their weeks.** DeepSeek V4.1 Flash (0.598),
  GLM-5.3 (0.593) and Qwen3.8-2.4T (0.519) are within each other's CIs, and each leaves ships without a window in 3
  or 4 weeks; Kimi K3 and GLM-5.3-Flash break one in 9, mostly overlapping berths and the crane pool.
- **Heeding the check:** confirming straight after a check that reported problems, Claude Opus 5.5 5%, Claude Haiku
  5.5 8%, GLM-5.3 9%, Claude Sonnet 5.5 11%, DeepSeek V4.1 Flash 20%, GPT-6 Luna 25%, Qwen3.8-2.4T and GPT-6 Astra
  26%, GPT-6.1 Sol 35%, GLM-5.3-Flash 36%, Kimi K3 41%, Qwen3.8-27B 96%.
- Every run passed the validity audit. Claude Sonnet 5.5's `dock-36A-w10x1-standard-0`, unscored in its first sweep
  (a reply that never came, then an attempt stopped by hand), was played again for this board.

**v2, the live port**, the same twelve models, one run per model and week. On the same weeks the rolling re-planner
scores 1.000 and the naive policy 0.202:

<!-- board:v2 -->

<!-- /board:v2 -->

- **Four models score above 0.9 and break no rule:** GPT-6 Astra (0.984), Claude Opus 5.5 (0.976), GPT-6.1 Sol
  (0.957) and Claude Sonnet 5.5 (0.904). Astra plays 11 of the 15 weeks to the optimum.
- **DeepSeek V4.1 Flash (0.754) and GLM-5.3 (0.748) lead the open models,** ahead of Claude Haiku 5.5 (0.694), which
  keeps every week feasible but plays none to the optimum.
- **Kimi K3 and GLM-5.3-Flash break a rule in 8 of their weeks, Qwen3.8-27B in all 15,** GPT-6 Luna in 3.
- Every run passed the validity audit. Three of Claude Opus 5.5's weeks, lost when the Docker VM restarted mid-run,
  were played again (`live-opus-2`), and so was Qwen3.8-2.4T's `dock-24B-w16x1-busy-0`, which had stopped at its cost
  cap, with a $10 cap (`live-qwen2t-3`).

**v1, a week planned in one go**, on ten eval weeks, next to PortSimEnv's published eval of the same weeks:

| Model | Mean of 10 weeks | Published, same weeks |
|---|---:|---:|
| GPT-6.1 Sol | 0.907 | 0.872 |
| Claude Sonnet 5.5 | 0.778 | 0.839 |

One Sonnet episode, on the 56-ship storm week `dock-36A-w15x2-storm-0`, spent both of its turns' 32,000 output tokens
without calling a tool and scored 0; PortSimEnv's harness ends such an episode the same way.

## Limitations

- **Small samples:** one run per model and week, 15 weeks in v2, v3 and v4 (twelve models) and 10 in v1 (two). The
  intervals above are wide, and a single week can swing by a lot. The 15 wind weeks rest on 11 schedules and 10
  weather weeks; 2025-W03 alone serves 4 of them, and one is a false alarm.
- **Providers:** the open models ran on Fireworks, and Qwen3.8-27B on Groq with its limit of 16,384 output tokens a
  reply, not on the providers PortSimEnv's eval used through the Hugging Face router; the same weights can score
  differently on another provider. A week that hit its episode's cost cap was played again with a higher one: Kimi
  K3's `dock-24B-w07x1-busy-0-e09` (v4, $12) and Qwen3.8-2.4T's `dock-24B-w16x1-busy-0` (v2, $10).
- **Simulated pressure on real data:** the ships, their calls, the cranes, the port's rules and its other traffic are
  real; the workloads and the disruptions are simulated, except v4's storms and forecasts, and the parties send
  scripted news without answering the agent.
- **v4's weather is transplanted:** each wind week is a 2024 marine week moved, hour for hour, into a weather week of
  2023 to 2025. Its ships never met that wind, and the task keeps its 2024 week, so no real date reaches the agent.
- **Readings partly unvalidated:** Y7's readings count as published, validated or not. The windows of the 9 weather
  weeks from 2023-W44 to 2025-W03, 5 of which set 10 of the 15 wind weeks, rest wholly on readings not yet validated;
  `wind_windows` gives each window's share. Hours with no reading at all count as calm: 17 hours after the working
  week in 2024-W18 (`e07`), and hour 126 in 2025-W03 (`e12`).
- **A stand-in forecast:** the port's own forecasts aren't published. The Port Control bulletin stands in for them with
  ECMWF's open-data runs at the nearest sea grid point, calibrated to Y7 by quantile maps fitted on another year, and a
  run counting as published 9 hours after its start is an assumption. The runs are only as good as that: at 9 to 72
  hours ahead they showed 41% to 62% of the hours that blew above 25 kn, 31% to 69% of the hours they showed above 25 kn
  didn't blow, and 2024's and 2025's runs showed only 7 of the 138 hours that blew above 30 kn. A storm's 30 kn core
  mostly comes unforecast, and is excused; following the forecast pays through the 25 kn windows.
- **One anemometer:** the whole port's wind is read at Y7, Port de Barcelona – Bocana Sud, which stands in for the
  ordinance's Dique Sur anemometer. Y7 publishes a 30-minute mean and a 3-second gust; the factors that turn them into
  the ordinance's 10-minute and 1-minute means are assumptions.
- **v4's simplifications:** the ordinance's thresholds start a review with the pilots, which PortSimEnv simplifies to
  no-movement windows; windows with gaps of 2 hours or less between them are merged; forecast watches come only at
  00:00 or 12:00. The harness sees the watch count, which depends on the forecasts to come, though the agent's tools
  and turns don't. In an infeasible week the whole-plan excuse can give different partial credit from the marine
  port's. The plugin
  README's [wind rules and their sources](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.4.3/README.md#the-wind-rules-and-their-sources)
  marks each assumption.
- **v3's assumptions:** some numbers have no public source, among them the 7 pilots on duty (calibrated to the 2024
  traffic), the tugs per ship length, and the cuts. Ships don't wait for a tug: a short hour is a rule break. The
  plugin README's [rules and their sources](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.4.3/README.md#the-rules-and-their-sources)
  marks each one. v4 keeps them.
- **Eval weeks only:** live, marine and wind weeks are qualified from the eval pack; the training weeks are in
  PortSimEnv's dataset and play on v1.
- **Spend** is computed from token usage at prices pinned in October 2026, not billed amounts; a request whose usage
  never arrived counts at the most it could have cost.

## Licence and attribution

The dataset carries several sets of terms, hence `license: other`; the plugin's
[data/LICENSE](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.4.3/data/LICENSE) and
[NOTICE](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.4.3/NOTICE) set out each file.

**CC BY-SA 4.0: the weeks, the tables, the references and the transcripts**, except v4's weather. The weeks come from
PortSimEnv's dock-v1 task packs, which Adithya S Kolavi built from the Port of Barcelona's 2024 container calls and
shared under CC BY-SA 4.0. The other traffic in v3 and v4 is derived from the port's record of its 2024 calls of
every ship type (`Barcelona_2024.csv` in
[alberto-santini/berth-allocation-problems](https://github.com/alberto-santini/berth-allocation-problems),
CC BY-SA 4.0). Contains data from the [Port de Barcelona open data portal](https://opendata.portdebarcelona.cat/). The
tables, the references and the transcripts, which carry the task text, are derived from them under the same licence.

**v4's weather keeps its two sources' terms**, not CC BY-SA 4.0. It is in `v4_tasks`, `v4_episodes`,
`v4_references`, the `dock-v1-eval-wind` tables, `raw/dock-v1-eval-wind.jsonl`, `bundles/dock-v1-eval-wind/`,
`references/wind.*` and the `runs/wind-*` sweeps.

*The forecasts, CC BY 4.0.* The forecast knots and windows are modified ECMWF open data:

> Copyright: © 2023-2026 European Centre for Medium-Range Weather Forecasts (ECMWF).
>
> Source: www.ecmwf.int
>
> Licence Statement: This data is published under a Creative Commons Attribution 4.0 International (CC BY 4.0).
> https://creativecommons.org/licenses/by/4.0/
>
> Disclaimer: ECMWF does not accept any liability whatsoever for any error or omission in the data, their
> availability, or for any loss or damage arising from their use.
>
> This data is based on data and products of the European Centre for Medium-Range Weather Forecasts (ECMWF).
>
> Modified: each run's 10 m wind at one grid point, every 3 hours to 72 hours, mapped to the Y7 anemometer by
> quantiles and rounded to whole knots.
>
> Terms of use: https://apps.ecmwf.int/datasets/licences/general/

*The observed wind, Meteocat's terms.* The windows that blew are derived from the readings of the Servei Meteorològic
de Catalunya's (Meteocat) XEMA station Y7, Port de Barcelona – Bocana Sud, in the Generalitat de Catalunya's open data
portal ([nzvn-apee](https://analisi.transparenciacatalunya.cat/d/nzvn-apee)). No reading is included, and the windows
are subject to the terms published there ([Meteocat's legal notice](https://www.meteo.cat/wpweb/avis-legal/)):

> Font: Servei Meteorològic de Catalunya (Meteocat), estació XEMA Y7; dades extretes el 2026-10-08; finestres derivades

**Apache-2.0: the verifier scripts in `bundles/`**, from the plugin.

The films and the replay Space draw the port on a 3D twin © OpenStreetMap contributors (ODbL), with terrain from
Terrain Tiles (AWS); the twin is not in this dataset. A wind film's forecast strip carries the ECMWF and Meteocat
credit: keep it, with the OpenStreetMap attribution, on anything you publish from a film.

`scripts/hub_dataset.py` in the plugin builds this dataset with agentenv-hf: PortSim's tables from the plugin's
checkout and the recorded sweeps, and agentenv-hf's tables, raw records, bundles and this card's `agentenv` table as
`agent-env hf publish` writes them, after agentenv-hf's scan of every file for keys and token shapes.

This dataset is independent: neither the Port de Barcelona, PortSimEnv's author, ECMWF nor Meteocat is affiliated
with it or endorses it.
