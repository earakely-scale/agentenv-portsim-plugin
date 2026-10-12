---
license: other
license_name: cc-by-sa-4.0-cc-by-4.0-meteocat-apache-2.0
license_link: https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/data/LICENSE
pretty_name: PortSimEnv on AgentEnv
language:
- en
task_categories:
- reinforcement-learning
- text-generation
size_categories:
- 1K<n<10K
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
- multi-agent
configs:
- config_name: v5_tasks
  default: true
  data_files:
  - split: eval
    path: tasks/v5.parquet
- config_name: results
  data_files:
  - split: eval
    path: results/board.parquet
- config_name: v5_episodes
  data_files:
  - split: eval
    path: episodes/v5.parquet
- config_name: v5_references
  data_files:
  - split: eval
    path: references/lines.parquet
- config_name: v4_tasks
  data_files:
  - split: eval
    path: tasks/v4.parquet
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
  default: dock-v1-eval-lines
---

# PortSimEnv on AgentEnv

[![GPT-6 Astra plays a lines week at the Port of Barcelona: the watch panel lists each arrival time it requests from the ships' agents and their answers, agreed or refused, while the agents' ETAs and arrival calls arrive as bulletins and ships slowed on request berth as they get in](https://raw.githubusercontent.com/earakely-scale/agentenv-portsim-plugin/v0.5.2/assets/lines-port.webp)](https://earakely-scale-portsimenv-agentenv.hf.space/viewer/#/run/lines-astra/openai%2Fgpt-6-astra/dock-36A-w05x1-busy-0-e09)

<sub>GPT-6 Astra plays the lines week `dock-36A-w05x1-busy-0-e09`, Terminal Catalunya (BEST)'s busy week of 29 January
2024 in the wind of the storm week of 11 November 2024. Its 27 ships belong to 7 shipping agents, each its own A2A
agent that reports its ships' ETAs as they near and answers the planner's `message_agent`. Astra requests an arrival
hour for every ship, 54 requests in 28 messages: 23 come back "can't arrive that early" and it asks again, until all
27 ships have an agreed arrival, 11 of the agreements slowing a ship down. No ship waits at anchor, and the week costs
413, what the plan in hindsight, which knows every arrival, costs: reward 1.0. The follower re-planner, which also
asks, costs 539 (0.339); the same re-planner never asking, and v2's naive policy, break rules (0.119 and 0.163).
**▶ [Watch this week](https://earakely-scale-portsimenv-agentenv.hf.space/viewer/#/run/lines-astra/openai%2Fgpt-6-astra/dock-36A-w05x1-busy-0-e09)**
on the [replay Space](https://huggingface.co/spaces/earakely-scale/PortSimEnv-AgentEnv), or the
[full film](https://github.com/earakely-scale/agentenv-portsim-plugin/releases/tag/replays-2026-10-11). Twin ©
OpenStreetMap contributors (ODbL); forecasts ECMWF open data (CC BY 4.0, modified); wind windows derived from Meteocat
XEMA Y7.</sub>

An agent runs one container quay at the Port of Barcelona for a week of 2024 that has just gone wrong: late and
bunched ships, closed quay sections, crane breakdowns, gales, emergencies. It decides when, where along the quay and
with how many cranes every ship docks, and the week is graded deterministically, with no judge, against plans the
CP-SAT solver finds. The ships and their calls, the quays' crane fleets and the port's berth and wind rules are real;
the workloads and the disruptions are simulated, except in v4 and v5, where the storms and their forecasts are real.
This dataset holds the weeks and the recorded runs of that environment on the
[AgentEnv Framework](https://www.agentenvframework.com), in five versions:

- **v5, the lines port** (env `portsim-lines`): v4's wind week with the shipping lines answering back. Each ship's
  agent, the firm the port's 2024 record names for its call, is its own A2A agent, which the planner messages with a
  `message_agent` tool. The agents' ETAs firm up as their ships near, a ship agrees a requested arrival time when it
  can make it by slowing down, ships berth first come, first served, and an hour at anchor costs what an hour late
  does. As in v4, the week is graded against the lower of the hindsight optimum and a re-planner's best cost
  ([The lines port](#the-lines-port-v5)).
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

| | PortSimEnv in FineEnvs | PortSimEnv on AgentEnv |
|---|---|---|
| Environment and code | [FineEnvs/PortSimEnv](https://huggingface.co/spaces/FineEnvs/PortSimEnv) (OpenEnv Space), [code](https://github.com/adithya-s-k/FineEnvs/tree/main/07-simulation-environments/portsim-v1) | [earakely-scale/agentenv-portsim-plugin](https://github.com/earakely-scale/agentenv-portsim-plugin) |
| Eval | [FineEnvs/PortSimEnv-Eval](https://huggingface.co/spaces/FineEnvs/PortSimEnv-Eval) | the `results` table, [Results](#results), [model board](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/results/board.md) |
| Dataset | [FineEnvs/PortSimEnv](https://huggingface.co/datasets/FineEnvs/PortSimEnv) | this dataset |
| Replays | | [earakely-scale/PortSimEnv-AgentEnv](https://huggingface.co/spaces/earakely-scale/PortSimEnv-AgentEnv) |
| Article | [Simulation RL Environments, part 1](https://huggingface.co/spaces/FineEnvs/simulation-rl-environments) | |
| What's next | [Discussion #36](https://github.com/adithya-s-k/FineEnvs/discussions/36) | |

## The lines port (v5)

v5 plays v4's 15 wind weeks with the shipping lines answering back. Every ship has its agent: the shipping agent the
Port de Barcelona's record of its 2024 calls names for the call, such as Hapag-Lloyd Spain or Noatum Maritime. Each
agent with ships in the week is deployed as its own A2A agent (`portsim-line`, named by the firm's id) and peered with
the planner, whose model gets a `message_agent` tool; a week has 7 to 9 agents for its 14 to 28 ships. An agent has no
model: it answers from the env, so the same messages always get the same replies. What v5 adds to the wind week:

- **A schedule that is an estimate.** The published schedule is the line's estimate from 72 hours out: each ship
  arrives at its scheduled hour plus its agent's long-range error, mostly later, so the schedule doesn't give the
  truth away.
- **ETAs that firm up.** Each ship's agent reports its ETA 48 and 24 hours out, and the ship calls in an hour before
  it reaches buoy S; a report made between watches arrives with the next bulletin. An ETA is off by 20% of the hours
  left, counted to 72 at most, scaled by the ship's bias, and mostly early: most ships arrive later than their agent
  says, by less as they near, and the call is exact. The notices of a late ship, a bunch of ships or an unscheduled
  call give their agents' ETAs, not the hours the ships really arrive.
- **Requested arrival times.** `message_agent(agent, requests)` asks one agent for its ships' latest ETAs or requests
  an arrival hour, up to 20 requests a message, each `{"ship": 7, "ask": "eta", "request_arrival": null}` or
  `{"ship": 9, "ask": null, "request_arrival": 130}`. An agent commits to an hour once its ship has sailed from its
  previous port or its own estimate is within 48 hours; before that it replies that it can't commit yet and gives its
  ETA. Then it agrees an hour the ship can make at its cruising 17 kn, or by slowing to as little as 10 kn once it has
  sailed, and the ship arrives at that hour; otherwise it offers the earliest or the latest hour the ship can make,
  which can be agreed at once. A refusal for a ship already agreed restates the agreement.
- **News can undo an agreement.** Until the port's news about a delayed or bunched ship, its agent works from the plan
  as it stood. At the news, an earlier agreement stands if the ship, on its true track at the paces its agreements
  set, can still make that hour; otherwise it lapses and the ship cruises in from where it is. Without an agreement,
  the notice's ETA is what the agent last said, moved later by the delay.
- **The port berths late ships.** A ship that gets in after its window starts is berthed by the port at the first hour
  a free stretch of quay fits it, nearest its planned sections and with the same cranes, around every other window
  without breaking a rule and never ahead of an earlier agreed ship still waiting; nobody else moves. A ship that gets
  in before its window waits at anchor for it.
- **First come, first served, for agreed ships.** No ship may start berthing while an earlier ship whose arrival was
  agreed waits at anchor, unless the wind holds that ship or the closures leave no stretch of quay long enough for its
  stay. A ship's turn is when it would arrive at cruising speed, so a ship slowed on request keeps its turn.
- **An hour at anchor costs an hour late:** each hour a ship waits between its arrival and its berthing costs its
  sections.

Besides `message_agent`, the planner's tools change three ways: `get_situation` shows where the port would berth a late
ship (`port_berth_hour`, `port_section`, on its latest ETA until it is in), `confirm_berths` also returns the confirmed
plan's problems and cost, as `check_plan` does, and `advance` returns only the watch, the hour and the freeze line. The
env was validated in six rounds of GPT-6 Astra runs, each followed by an independent recomputation of every agent reply,
notice, report, window row, confirm result and port placement; the last round found no mismatch in about 299,000 env
answers.

**How it is graded.** As v4, on the windows confirmed, as the port runs them, and the week as it really happened, in the
wind that blew. The cost adds each ship's hours at anchor, and a rule break is what the confirmed windows break among
themselves, or a ship berthing while an earlier agreed ship waits; any rule break makes the week infeasible. The excuse
is v4's, and an ETA that proves wrong is not news to it: it weighs every window against the ships' real arrivals, so
what a ship arriving off its agent's ETA brings is charged. Rewards are scored against the **anchor**, as in v4 the
lower of the **hindsight** cost and the **follower**'s best over its 4 solver configurations. Hindsight is CP-SAT
knowing every arrival: it asks each ship at the first watch its agent could commit, and not before its news, and
protects in the queue only the ships it slows. It is the anchor in 13 of the 15 weeks. The follower is a CP-SAT
re-planner that re-plans at every watch on the arrivals as known and requests arrival times through the agents, for each
ship whose window would freeze before the next watch, each ship it plans to slow and each ship due within 12 hours of
the next watch, taking each counter-offer; its best cost is 0.78 to 2.25 times hindsight's, and it scores 0.548 in its
first configuration. The **silent** follower re-plans the same way but never asks the agents (0.242), and the naive
policy is v2's (0.184). The references keep the queue stricter than the grade, with no wind or closure exception, so a
planner that uses an exception can beat the anchor and score 1.0. A week qualifies when (a) at least 3 of the follower's
4 configurations finish feasible, (b) the silent follower scores 0.9 or less in at least 3 of its 4, so asking the
agents matters, and (c) the week has at most 10 watches; all 15 wind weeks do.

**Where the agents come from, and what is assumed.** The sources, each assumption marked; the pack's manifest
([data/dock-v1-lines/manifest.json](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/data/dock-v1-lines/manifest.json))
carries most of them in brief:

- *The agents:* the shipping agent (`CONSIGNATARI`) of each call in the Port de Barcelona's 2024 calls of every ship
  type, the record v3's other traffic comes from (CC BY-SA 4.0); an unscheduled call takes its ship's nearest 2024
  call.
- *The distances:* each ship's previous port's distance from
  [NGA Pub. 151, Distances Between Ports](https://maritimesafetyinnovationlab.org/wp-content/uploads/2015/01/pub151-distances-btw-ports.pdf),
  a work of the United States government on which no copyright is claimed. A ship can slow only once it has left that
  port.
- *The reports:* Directive 2002/59/EC (art. 4) and Orden FOM/1194/2011 (art. 9) require a notice at least 24 hours
  before arrival, the IMO Just In Time Arrival Guide (2020) puts berth planning at about 48 hours, and the 2025
  berthing ordinance (BOE-A-2025-5157) defines arrival by the call an hour before buoy S. The 48-hour report and the
  delivery at the next watch are assumptions.
- *The ETA error*, an assumption inside the published range: off by 20% of the hours left on average, counted to 72
  at most, with 80% of ships later than their ETA, and each ship's bias drawn; the published schedule is the same
  estimate from 72 hours out. Published: agents' ETAs 24 to 48 hours out off by 5 h 15 min on average at Busan New
  Port (2022-23) and by 10 to 15 hours at Antwerp (2019), and 80% of arrivals later than the leg's ETA on MSC's
  Barcelona-Valencia loop (2017-18).
- *The commitment and the requests:* an agent commits once its ship has sailed or its estimate is within 48 hours, the
  IMO Just In Time Arrival Guide's berth-planning horizon, and answers a request it can't meet with the earliest or the
  latest hour the ship can make, after the guide's requested time of arrival.
- *The speeds*, assumptions: cruising 17 kn and slowing to 10 kn, inside the 12 to 20 kn of MSC's Barcelona-Valencia
  loop and the 10 kn economical speed of the IMO's Just In Time container study.
- *The queue:* Barcelona's container terminals berthed first come, first served in 2024, and the 2025 ordinance made
  it the general rule (art. 3), exempting a ship the quay can't take. A slowed ship keeping its turn is the
  virtual-arrival arrangement; holding the queue only for agreed ships is an assumption, and the ordinance's other
  exceptions are left out.
- *The news and the late ships*, assumptions: an agreement survives a delay only if the ship can still make it, and
  the port berths a ship that misses its window at its next free slot, moving nobody else.
- *The anchor cost*, an assumption: an hour at anchor costs the same as an hour late, the round value inside the
  evidence (the fuel a ship saves by slowing instead of waiting is worth 1.3 to 1.8 hours of its charter, and an hour
  late costs more than the charter alone).

The lines weeks keep v4's weather, and so its terms ([Licence and attribution](#licence-and-attribution)).

## Tables

Two kinds of tables, all parquet, all under the split `eval` (for the words they use, see [Terms](#terms)). PortSim's
own, one family per version:

| Config | Split | Rows | What |
|---|---|---:|---|
| `v5_tasks` (default) | `eval` | 15 | the lines weeks: what the agent is told at the start, with the ships' agents and the arrivals as known, each watch's news with the agents' ETA reports and Port Control's forecast, the wind that blew, and the reference costs |
| `results` | `eval` | 38 | the model board: one row per version and model, with its mean reward over the weeks and its 95% CI, each tier's mean, and how many weeks it finished, kept feasible and played to the optimum (v4 and v5: the anchor), with its tokens, cost and time ([Results](#results)) |
| `v5_episodes` | `eval` | – | models on the lines weeks: the grade, the hours ships waited at anchor, every request to the ships' agents with its reply, the tool calls and the full transcript |
| `v5_references` | `eval` | 15 | for each lines week, the hindsight optimum, the follower, the silent follower and the naive policy, and the conditions it qualified on |
| `v4_tasks` | `eval` | 15 | the wind weeks: what the agent is told at the start, each watch's news with Port Control's forecast, the wind that blew, and the reference costs |
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
| `dock-v1-eval-lines_tasks`, `dock-v1-eval-lines_episodes` | `eval` | 15, – | `bundles/dock-v1-eval-lines` | v5 |
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
false alarm, on `dock-24B-w07x1-busy-0`. They use 11 of the marine weeks' schedules, three of them more than once. A
lines week is a wind week with its ships' agents, and all 15 qualify (see [The lines port](#the-lines-port-v5)).

A task id reads `dock-<quay>-w<week>x<weeks>-<difficulty>-<seed>`: `dock-24B-w07x1-busy-0` is week 7 of 2024 at quay
24B, one week long, busy tier. A wind week adds its weather week, `-e00` to `-e15`: `dock-24B-w37x1-standard-0-e01` is
the marine week `dock-24B-w37x1-standard-0` in the wind of 2023-W10. A lines week keeps its wind week's id. A v1 task
can span up to three weeks (`x2`, `x3`); a v2 to v5 week is always one. `dock-v1` is the name of PortSimEnv's task
pack, which all five versions use, not this dataset's version.

## Terms

- **Week**: one task, a quay with its ships and what goes wrong. **Watch** (v2 to v5): watch 0 opens the week at
  hour 0, and a new watch starts at each news bulletin; the agent re-plans each watch, and a window starting within 6
  hours (the freeze) can no longer change. A wind week has 4 to 10 watches and always 52 turns, those of 10 watches,
  so the turns don't give the count away; a lines week, with the same watches, always 72, 7 a watch for its messages;
  v2 and v3 weeks have 47. **Validity audit** (v2 to v5): the env's check that every bulletin arrived once, on time,
  at its watch, and in v5 that every ship whose arrival was agreed arrived then; a run that fails it is not scored.
- **Pilots and tugs** (v3 to v5): a pilot is the local mariner who boards to guide a ship in or out of the port, and
  tugs are the boats that push and pull it alongside. Every berthing and departure of a ship of 45 m or more takes a
  pilot, and tugs by length (0 under 120 m, up to 3 from 300 m), in its hour, from 7 pilots and 8 tugs on duty; inside
  an announced gale window (in v4 and v5, in wind above 25 kn) most movements take one more tug (not Ro-Ro ships and
  ferries under 200 m, nor yachts).
  The port's other 2024 calls use the same pools. In any hour the quay's ships may need no more than are free; a
  short hour is a rule break.
- **Wind rules** (v4, v5): above 25 kn (10-minute mean), ships of 300 m or more may not berth or leave and every
  movement takes one more tug, with the exemptions above; above 30 kn no ship moves (the port's traffic ordinance,
  BOE-A-2023-6719). The wind is read at Meteocat's XEMA station Y7, which stands in for the ordinance's Dique Sur
  anemometer, and the hours it blew above each threshold are the week's no-movement windows; a range a–b runs from
  hour a up to, not including, hour b. v3's gale is gone; the agent sees only forecasts and the wind observed so far.
- **Forecast bulletin** (v4, v5): at every watch a Barcelona Port Control bulletin, standing in for the port's own
  forecasts, gives the latest ECMWF open-data (HRES) run published by then, adjusted to Y7 by quantile maps fitted on
  another year, in whole knots. A run counts as published 9 hours after it starts. The bulletin gives the hours above 25
  and 30 kn it shows and its peak; the situation adds its knots every 3 hours. A watch is added at 00:00 or 12:00 when
  the run in force then shows an hour above 25 or 30 kn, 6 to 42 hours ahead, that the run at the watch before didn't.
- **Storm week, false-alarm week** (v4, v5): the weather weeks a wind or lines week is set in. A storm week had a
  window above 25 kn of 4 hours or more, or an hour above 30 kn, at Y7; a false-alarm week (`bust` in the tables)
  stayed below that, though its forecasts showed hours above 25 kn that didn't blow. The 14 wind weeks set in a storm
  week are the storm wind weeks.
- **Ship's agent** (v5): the firm that deals with the port for a ship's line, as the port's 2024 record names it for the
  call; each is its own A2A agent, which the planner messages. **ETA**: an agent's estimate of the hour its ship
  arrives; the published schedule is the same estimate from 72 hours out. **Agreed arrival**: an hour a ship's agent has
  agreed, once the ship has sailed or its estimate is within 48 hours; the ship arrives then, unless news makes the hour
  impossible and the agreement lapses. **Turn**: a ship's place in the first-come, first-served queue, the hour it would
  arrive at cruising speed; the queue holds for the ships whose arrival was agreed. **Hours at anchor**: the hours ships
  wait between their arrival and their berthing, each charged as an hour late. **Port berth**: where the port berths a
  ship that gets in after its window starts, at the first hour a free stretch of quay fits it.
- **Optimum**: the cost of the best plan CP-SAT, a constraint solver, finds for the week as it really happened. A
  **solver configuration** is one of the 4 ways the references run CP-SAT: 1 or 8 workers, each with or without an
  earliest-finish tie-break. **Hindsight** (v4, v5): that optimum with the whole week known, in the wind that blew; in
  v5 it also knows every arrival, asks each ship at the first watch its agent could commit, and not before its news,
  and protects in the queue only the ships it slows.
  **Anchor** (v4, v5): what the week scores against, its `optimal_cost`. In v4, the lower of the hindsight optimum and
  the forecast-following re-planner's best cost over its 4 solver configurations: the agent's cost is net of its
  excuses while hindsight pays for all the wind, so following the forecast can cost less than hindsight, and the
  anchor is below it in 5 of the 15 wind weeks. In v5, the lower of the hindsight cost and the follower's best cost
  over its 4 solver configurations: hindsight in 13 of the 15 lines weeks, the follower in the other 2.
- **Rolling**: a CP-SAT re-planner that only knows what has been announced; in v4 that includes the forecast, so it is
  the forecast-following re-planner. **Blind** (v4): the same re-planner with the wind taken out of the week as known.
  **Hold** (v4, the false-alarm week): the same, holding every window any forecast so far has shown. **Follower** (v5):
  the rolling re-planner on the arrivals as known, which requests arrival times through the ships' agents and takes
  their counter-offers (the references' `rolling` columns). **Silent** (v5): the same, never asking. **Naive**: a simple
  policy that pushes ships later (in v2 to v5, it keeps each confirmed window that still fits and moves the rest; it
  knows nothing of pilots and tugs, so in v3 it often breaks their rule). **Unavoidable**: the cost no plan avoids; in
  v4 and v5, in the wind that blew (the floor). **Regret**: cost above the optimum, in v4 and v5 above the anchor.
  **Excused cost**: cost the grade excuses, which is not charged: in v2 and v3, cost that news put on a frozen window;
  in v4 and v5, the cost the excuse waives.
- **The excuse** (v4, v5): per ship, at its freeze, on the whole plan. A ship first frozen at watch k is compared with
  the week as known at watch k−1, its news and its forecast, and a rule break or cost the week adds to that is excused,
  once. So wind that no forecast had shown by then is excused, and wind the forecast showed and that blew is charged, as
  an ignored warning. A problem ships share (an overlap, or pilots, tugs or the move limit short at an hour) is judged
  for each of them as the ship decided last saw it. In v5 an ETA that proves wrong is not news: what a ship arriving off
  its agent's ETA brings, lateness and hours at anchor, is charged; a ship whose arrival was agreed arrives at the
  agreed hour.
- **Reward**: 0.2 + 0.8·e^(−gap/0.5) for a valid plan, where gap = max(0, cost − optimum) / (max(0, optimum −
  unavoidable) + 100), so the optimum scores 1.0; in v4 and v5 the anchor and the floor take the optimum's and the
  unavoidable cost's places. A plan that breaks a rule scores under 0.2 (0.2 times the share of ships placed
  cleanly), and a run that submits nothing scores 0. The confidence intervals below are bootstrap intervals over
  weeks.
- **Sweep**: one batch of runs (models × weeks), recorded in `runs/`; the sweeps named `…-pilot-…` were small first
  batches of a few weeks, unrelated to harbour pilots. **Bundle**: a folder of agent-env tasks; `bundles/` has one per
  version.

## Use

```python
import json
from datasets import load_dataset

repo = "earakely-scale/PortSimEnv-AgentEnv"
weeks = load_dataset(repo, "v5_tasks", split="eval", revision="v0.5.2")
week = weeks[0]
# what the agent gets at hour 0
print(week["system_prompt"], week["situation"], sep="\n\n")
# the ships' agents the planner can message, each with its ships
print(json.loads(week["agents"]))
# what arrives later: the agents' ETA reports and arrival calls, Port Control's forecast and the rest
for watch in json.loads(week["watches"]):
    print(watch["hour"], [n["text"] for n in watch["notices"]])
# the wind that blew, which the grade reads
print(json.loads(week["wind_windows"]))

episodes = load_dataset(repo, "v4_episodes", split="eval", revision="v0.5.2")
# a list of chat messages: no json.loads
messages = episodes[0]["messages"]
call = next(c for m in messages if m["tool_calls"] for c in m["tool_calls"]
            if c["function"]["name"] == "check_plan")
# the arguments are an object
a = call["function"]["arguments"]
# the plan as sent: a JSON string from Claude Sonnet 5.5, a list from GPT-6.1 Sol
plan = a["plan"] if isinstance(a["plan"], list) else json.loads(a["plan"])
print(plan)

# a lines run's requests to the ships' agents, each with its reply
runs = load_dataset(repo, "v5_episodes", split="eval", revision="v0.5.2")
print(json.loads(runs[0]["exchanges"]))
```

`messages`, in every `vN_episodes` table, is now a list of chat messages, the type agentenv-hf writes: OpenAI roles,
`tool_calls` of `{id, type, function: {name, arguments}}` with `arguments` an object, and `tool_call_id` and `name`
on tool messages, which TRL's `SFTTrainer` and transformers chat templates read. In v0.3.x it was a JSON string. The
other columns holding JSON (`watches`, `wind_windows`, `agents`, `task`, the plans, `exchanges`, `steps`, and the
references' `rolling_plans`, `rolling_exchanges`, `configs`, `solver` and `clauses`) are still strings; `json.loads`
them. agentenv-hf's JSON columns (`scores`,
`verifications`, `structured_output` and its tasks' `steps`) come back as Python objects in `datasets` 5.1.

## Play a week yourself

You need Docker (running, usable without `sudo`, with buildx), [uv](https://docs.astral.sh/uv/) and git. Install
the plugin, which brings agentenv-hf with it, build the images, and check it all works with a free task that calls no
model:

```bash
uv tool install agentenv-framework \
    --with "agentenv-portsim @ git+https://github.com/earakely-scale/agentenv-portsim-plugin@v0.5.2"
# build the env and agent images and register them (a few minutes)
agent-env portsim setup --agent
# no model: grades a known optimal plan, prints "passed"
agent-env run portsim --task smoke
```

Then play a week straight from this dataset. You need a Hugging Face token with the "Make calls to Inference
Providers" permission, on an account with credits; the tasks set no cost cap.

```bash
# with "Make calls to Inference Providers", on an account with credits
export HF_TOKEN=hf_...
export LITELLM_BASE_URL=https://router.huggingface.co/v1 LITELLM_API_KEY=$HF_TOKEN
# the default bundle: dock-v1-eval-lines (v5)
agent-env hf run earakely-scale/PortSimEnv-AgentEnv@v0.5.2 \
    --task dock-36A-w06x1-standard-0-e07 --model zai-org/GLM-5.3-Flash:baseten
# v4; dock-v1-eval-marine is v3, dock-v1-eval-live v2, dock-v1-eval v1
agent-env hf run earakely-scale/PortSimEnv-AgentEnv@v0.5.2 --bundle dock-v1-eval-wind \
    --task dock-36A-w06x1-standard-0-e07 --model zai-org/GLM-5.3-Flash:baseten
```

`hf run` downloads this card and `bundles/` at the tag's commit into
`~/.cache/agentenv-hf/earakely-scale/PortSimEnv-AgentEnv/<commit>`, checks that the plugins the card's `agentenv`
table names are installed (it never installs them itself), shows what it will run and asks first: `--yes` skips the
question, and `--dry-run` runs nothing. Without `--bundle` it plays the card's default, `dock-v1-eval-lines`, which
deploys a `portsim-line` agent for each of the week's ships' agents beside the model's. `dock-36A-w06x1-standard-0-e07`
is the shortest lines and wind week, with 4 watches.

The open models priced for the router are `Qwen/Qwen3.8-2.4T-A95B:together`, `Qwen/Qwen3.8-27B:ovhcloud`,
`zai-org/GLM-5.3-Flash:baseten` and `zai-org/GLM-5.3:together`; closed models go through a LiteLLM proxy (the plugin
README's [Play a model](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/README.md#play-a-model)).
If a step fails, the plugin README's
[troubleshooting](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/README.md#run-it-yourself)
covers the usual causes (`agent-env` not on the PATH, port 5000 taken by macOS AirPlay).

## Replay and publish your own runs

To replay your own runs on the same viewer as the Space, play them as a sweep, which records each run under
`results/runs/<name>/`, then serve them. `--lines` plays lines weeks, `--wind` wind weeks, `--marine` and `--live`
play v3 and v2, and a sweep with none of them plays v1.

```bash
agent-env portsim sweep run --lines --name mine --models zai-org/GLM-5.3-Flash:baseten \
    --tasks dock-36A-w06x1-standard-0-e07 --episode-cap-usd 1 --cap-usd 3
# http://127.0.0.1:8237/viewer/
agent-env portsim view mine
```

To publish them as a Hub dataset of your own, give `agent-env hf publish` the sweep's bundle,
`results/runs/<name>/bundle`. Write it to a folder first and look, then push:

```bash
# look first
agent-env hf publish results/runs/mine/bundle --name dock-v1-eval-lines --out mine-dataset
# then push
agent-env hf publish results/runs/mine/bundle --name dock-v1-eval-lines --repo you/portsim-runs
```

It writes the same tables as this dataset's `dock-v1-eval-lines_*` configs, the raw records and the bundle, under the
split `train` unless `--split` names another, and pushes them in one commit; pushing needs a token with write access.
Before writing anything it scans every file for this machine's keys and for token shapes, and stops on a hit.
Transcripts are published as the agent wrote them, so read a run's `messages` before you make a dataset public.
`--requires` and `--setup` write what the bundle needs to the card, as this card's `agentenv` table does, for
`agent-env hf run` to check; [agentenv-hf's README](https://github.com/earakely-scale/agentenv-hf-plugin/blob/v0.3.0/README.md#publish)
lists every option. The plugin README covers sweeps and filming a run.

## Dataset structure

**Tasks** (`v5_tasks`, `v4_tasks`, `v3_tasks`, `v2_tasks`, `v1_tasks`), one row per week:

- `task_id`, `quay`, `terminal`, `difficulty` (standard, busy, storm or extreme), `week`, `week_start_utc`,
  `num_ships`, `num_disruptions`. A wind or lines week keeps its schedule's 2024 week.
- `system_prompt`, `situation`: the rules and the opening message, exactly as the agent receives them. In v3 to v5
  the situation has a "Pilots and tugs" section: the pools, the rule, the tugs each ship takes, and the pilots and
  tugs free for the quay's ships each hour. In v4 and v5 a "Wind at the Dique Sur" section follows it: the wind rules,
  the forecast in force, its knots every 3 hours and the wind observed so far. In v5 an "Arrivals and the ships'
  agents" section ends it: the agents' rules, each agent with its ships, and each ship's arrival as known (its
  published hour, its agent's latest ETA, an agreed hour or its arrival) and its previous port.
- `optimal_cost`: the cost of the best plan CP-SAT finds for the week as it really happened; in v4 and v5, the
  anchor. `naive_cost`: v1, a plan that pushes ships later; v2 to v5, the naive policy's cost, empty when its plan
  breaks a rule (`naive_feasible`).
- v2 to v5: `num_watches`, `watches` (each watch's hour and its notices: who sends it, the hour it is about, the
  text; in v4 and v5 one of them is Barcelona Port Control's forecast, and in v5 the agents' ETA reports and arrival
  calls come from their firms), `rolling_cost` (the rolling CP-SAT re-planner; in v5 the follower) and
  `unavoidable_cost` (what no plan avoids).
- v3 to v5: `pilots` and `tugs` (the pools on duty), `other_movements` (the number of berthings and departures of the
  port's other traffic the pools also serve; the movements themselves are in `task`). v3 only: `v2_optimal_cost` (the
  same week's optimum without pilots and tugs).
- v4 and v5: `schedule` (the marine week it is built on), `hindsight_cost`, `weather_id`
  (`e00` to `e15`), `weather_week` (the ISO week, e.g. `2023-W10`), `weather_monday_utc`, `weather_kind` (`storm` or
  `bust`), and `wind_windows`: the windows that blew, each with its `start` and `end` hour, `above_kn` (25 or 30) and
  `unvalidated`, the share of its Y7 readings not yet validated. The grade reads them; the agent sees only the wind
  observed before each watch.
- v4 only: `v3_optimal_cost` (the week's optimum in the marine port), `blind_cost` (empty when the blind plan breaks a
  rule) and `blind_feasible`.
- v5 only: `v4_optimal_cost` (the week's anchor in the wind port), `silent_cost` (empty when the silent follower's
  plan breaks a rule) and `silent_feasible`, `num_agents`, and `agents`: the week's ships' agents, each with `agent`
  (the id it is deployed under, which `message_agent` takes), `name` (the firm) and `ships` (the ids of the ships it
  handles).
- v1 only: `proven_optimal`, `optimal_plan`, `naive_plan`. A plan is a list of
  `{"ship": id, "berth_hour": h, "section": s, "cranes": c}`.
- `task`: the full week as the task pack has it, including every disruption (in v3 to v5 the pools and the other
  traffic's movements; in v4 and v5 the windows that blew and the forecast in force at each watch; in v5, under
  `rules.lines`, each ship's agent, its previous port's distance and its ETA bias); in v2 to v5 the agent learns the
  disruptions only as their notices arrive.

**Episodes** (`v5_episodes`, `v4_episodes`, `v3_episodes`, `v2_episodes`, `v1_episodes`), one row per model and
week:

- `episode_id` (the run, as in agentenv-hf's tables), `model`, `model_name`, `task_id`, `difficulty`, `quay`,
  `num_ships`.
- `reward` (0 to 1), `feasible`, `cost` (of the plan, or of the confirmed windows in v2 to v5), `optimal_cost` (in
  v4 and v5, the anchor).
- v2 to v5: `num_watches`, `regret` (cost above the optimum, in v4 and v5 above the anchor), `excused_cost` (cost
  excused, not charged). v1: `submitted`, `checks`.
- v5: `anchor_hours` (the hours the week's ships waited at anchor, each charged as an hour late), `agent_messages`
  (the requests the agent sent the ships' agents, ETA asks and arrival requests alike) and `exchanges` (each request
  with its reply: the watch and hour, the agent and the ship, `ask` (`eta` or `request_arrival`), the hour requested,
  and the reply: the ETA, or whether the ship agreed the hour and, if not, why).
- `turns`, `tool_calls`, `input_tokens`, `output_tokens`, `cost_usd` (model spend at prices pinned in October 2026),
  `seconds` (the episode's own time, as PortSimEnv's records count it), `wall_seconds` (the whole `agent-env run`:
  deploying the env and the agents, the episode and the grade), `end_reason`, `sweep` (the run it comes from); v2 to
  v5 `reached_end` (the agent played to the week's end; otherwise the week ran on to its end on the windows confirmed
  so far).
- `final_plan`: in v1 the plan the model submitted (`null` for the one run that submitted none, below); in v2 to v5
  the confirmed windows, as the verifier graded them. `steps` (each tool call with its plan), `messages` (the full
  transcript, as chat messages).

**Results** (`results`), one row per version and model, best first, from the episode tables: `version`, `env`,
`model`, `model_name`, `provider` (who served it), `weeks`, `runs`, `mean_reward` with its 95% CI (`ci_low`,
`ci_high`: a bootstrap over the weeks, drawn in task id order as the plugin's sweep reports do), `reward_standard`,
`reward_busy` (v1 also `reward_storm`, `reward_extreme`), `finished` (v1: submitted; v2 to v5: reached the week's end),
`feasible`, `optimal` (in v4 and v5, at the anchor), `median_turns`, `input_tokens`, `output_tokens`, `cost_usd`,
`cost_per_episode` and `median_seconds` (of the episodes' own time). `results/v5.json` (and `v4.json`, `v3.json`,
`v2.json`, `v1.json`) hold the same board in the shape of PortSimEnv's article data (`portsim-results.json`): `model`,
`key`, `n`, `mean`, `tiers`, `submitted`, `feasible`, `optimal`, `tokens_out`, `tokens_in`, `median_s`, plus `ci`,
`provider` and `cost_usd`. In v2 to v5 `submitted` counts the weeks played to their end, as nothing is submitted, and in
v4 and v5 `optimal` counts the weeks at the anchor; `median_s` is the median episode time, as in the article's data. A
version no model has played yet has no rows and no JSON.

**References** (`v5_references`, `v4_references`, `v3_references`, `v2_references`). v2 and v3 have one row per
one-week eval week: `qualifies`, `optimal_cost`, `unavoidable_cost`, `watch_hours`, the rolling re-planner's and the
naive policy's `cost`, `reward`, `feasible` and `excused_cost` (`rolling_cost` to `naive_excused_cost`),
`rolling_plans` (the rolling plans per watch), `configs` (each solver configuration's cost; in v4 and v5 also its
reward) and `solver` (the solver settings); v3 adds `v2_optimal_cost`. v4 has one row per wind week, with the same
columns (`optimal_cost` is the anchor) and `schedule`, `weather`, `kind`, `hindsight_cost`, `v3_optimal_cost`,
`added_watches` (the watches its forecasts added), the blind re-planner's `blind_cost` to `blind_excused_cost`, and
`clauses` (whether the week meets each of the four conditions above, `a` to `d`); in the false-alarm week, the
hold-every-warning re-planner's `hold_cost` to `hold_excused_cost`, empty in the storm wind weeks. v5 has one row per
lines week, with the same columns as v2's, where `optimal_cost` is the anchor and `rolling_*` the follower in its
first solver configuration, and `hindsight_cost`, `wind_optimal_cost` (the week's anchor in the wind
port), `ships`, `firms` (the number of its ships' agents), the silent follower's `silent_cost` to
`silent_excused_cost`, each player's hours at anchor (`rolling_anchor_hours`, `silent_anchor_hours`,
`naive_anchor_hours`), `rolling_exchanges` (the follower's requests to the agents: the watch, the ship, the hour
asked and whether it was agreed), `configs` (each configuration also with its hours at anchor and its messages) and
`clauses` (the three conditions in [The lines port](#the-lines-port-v5), `a` to `c`).

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

Twelve models, once each on every lines, wind, marine and live week, with the same harness, prompts, tools and
limits: the mean reward on each version and over all 60 weeks, each week weighing the same. The plugin's
[results/board.md](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/results/board.md) analyses
them.

**Not comparable with PortSimEnv's v1 eval** ([FineEnvs/PortSimEnv-Eval](https://huggingface.co/spaces/FineEnvs/PortSimEnv-Eval)).
These are new environments, played another way: the agent re-plans the week as it unfolds, with four tools
(`get_situation`, `check_plan`, `confirm_berths`, `advance`), at most 3 planning calls a watch and 47 turns a week (52
on the wind port, and 72 on the lines port, which adds `message_agent`), where v1 plans the whole week in one go with
12 turns, 10 checks and one `submit_plan`. Each version plays 15 weeks drawn from the one-week standard and busy eval
weeks on which a rolling re-planner reaches the optimum, where v1's eval plays 50 weeks across four tiers. Rankings
don't carry over either: on v1, GLM-5.3-Flash scores above GLM-5.3; here it scores below.

<!-- board:all -->

<!-- /board:all -->

**v5, the lines port**, one run per model and week, on the same harness, prompts, tools and limits as v4, with
`message_agent` and 72 turns a week. Rewards are against the anchor, the plan in hindsight on every week. On the same
weeks the follower scores 0.485 in its first solver configuration (0.531 at its best), the silent follower 0.116 and
the naive policy 0.137; neither of those two keeps a week feasible. The models that agree an arrival for nearly every
ship lead: GPT-6 Astra and GPT-6.1 Sol agree 95% and 92% of a week's ships, Claude Opus and Sonnet 5.5 about half,
Claude Haiku 5.5 and GPT-6 Luna 14% and 11%, and most rule breaks land on ships left unagreed, whose windows slide
when they arrive late. Among the open models Kimi K3 agrees 49%, Qwen3.8-2.4T and GLM-5.3-Flash 43%, and none keeps
more than 2 weeks feasible; GLM-5.3 and DeepSeek V4.1 Flash end 11 and 9 of their weeks by reasoning past the
32,000-token reply limit twice in a row, mostly before confirming a window. Over all 60 weeks GPT-6 Astra leads at
0.882, ahead of Claude Opus 5.5 at 0.787.

<!-- board:v5 -->

<!-- /board:v5 -->

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
- **The best open model is Qwen3.8-2.4T** (0.662), above Claude Haiku 5.5 (0.583) but within noise: 0.926 on the
  three standard weeks, 0.596 on the busy ones, and feasible in 10 of 15.
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
- **DeepSeek V4.1 Flash (0.754) and GLM-5.3 (0.748) lead the open models,** above Claude Haiku 5.5 (0.694) but within
  noise. Haiku keeps every week feasible but plays none to the optimum.
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

- **Small samples:** one run per model and week, 15 weeks in v2 to v5 (twelve models) and 10 in v1 (two).
  The intervals above are wide, and a single week can swing by a lot. The 15 wind weeks, and so the 15 lines weeks,
  rest on 11 schedules and 10 weather weeks; 2025-W03 alone serves 4 of them, and one is a false alarm.
- **Providers:** the open models ran on Fireworks, and Qwen3.8-27B on Groq with its limit of 16,384 output tokens a
  reply, not on the providers PortSimEnv's eval used through the Hugging Face router; the same weights can score
  differently on another provider. A week that hit its episode's cost cap was played again with a higher one: Kimi
  K3's `dock-24B-w07x1-busy-0-e09` (v4, $12) and Qwen3.8-2.4T's `dock-24B-w16x1-busy-0` (v2, $10).
- **Simulated pressure on real data:** the ships, their calls, the cranes, the port's rules and its other traffic are
  real; the workloads and the disruptions are simulated, except the storms and forecasts of v4 and v5. In v1 to v4 the
  parties send scripted news without answering the agent.
- **v5's agents answer by rule:** no model plays the ships' agents. They report on schedule, give the ETA error the
  week drew for their ship, and agree any hour the ship can make; they don't bargain, refuse for their own reasons or
  run late on a promise. Each ship's previous port and the firm come from its 2024 call, but its ETA error, its speeds,
  the 48-hour report and the cost of an hour at anchor are assumptions inside published ranges
  ([The lines port](#the-lines-port-v5) gives each one's source), and the 2025 ordinance's exceptions to first come,
  first served other than the wind are left out.
- **The weather of v4 and v5 is transplanted:** each wind week, and so each lines week, is a 2024 marine week moved,
  hour for hour, into a weather week of 2023 to 2025. Its ships never met that wind, and the task keeps its 2024 week,
  so no real date reaches the agent.
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
- **v4's simplifications**, which v5 keeps: the ordinance's thresholds start a review with the pilots, which PortSimEnv
  simplifies to no-movement windows; windows with gaps of 2 hours or less between them are merged; forecast watches come
  only at 00:00 or 12:00. The harness sees the watch count, which depends on the forecasts to come, though the agent's
  tools and turns don't. In an infeasible week the whole-plan excuse can give different partial credit from the marine
  port's. The plugin
  README's [wind rules and their sources](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/README.md#the-wind-rules-and-their-sources)
  marks each assumption.
- **v3's assumptions:** some numbers have no public source, among them the 7 pilots on duty (calibrated to the 2024
  traffic), the tugs per ship length, and the cuts. Ships don't wait for a tug: a short hour is a rule break. The
  plugin README's [rules and their sources](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/README.md#the-rules-and-their-sources)
  marks each one. v4 and v5 keep them.
- **Eval weeks only:** live, marine, wind and lines weeks are qualified from the eval pack; the training weeks are in
  PortSimEnv's dataset and play on v1.
- **Spend** is computed from token usage at prices pinned in October 2026, not billed amounts; a request whose usage
  never arrived counts at the most it could have cost.

## Licence and attribution

The dataset carries several sets of terms, hence `license: other`; the plugin's
[data/LICENSE](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/data/LICENSE) and
[NOTICE](https://github.com/earakely-scale/agentenv-portsim-plugin/blob/v0.5.2/NOTICE) set out each file.

**CC BY-SA 4.0: the weeks, the tables, the references and the transcripts**, except the weather of v4 and v5. The weeks
come from PortSimEnv's dock-v1 task packs, which Adithya S Kolavi built from the Port of Barcelona's 2024 container
calls and shared under CC BY-SA 4.0. The other traffic in v3 to v5, and v5's ships' agents, are derived from the
port's record of its 2024 calls of every ship type (`Barcelona_2024.csv` in
[alberto-santini/berth-allocation-problems](https://github.com/alberto-santini/berth-allocation-problems),
CC BY-SA 4.0). Contains data from the [Port de Barcelona open data portal](https://opendata.portdebarcelona.cat/). The
tables, the references and the transcripts, which carry the task text, are derived from them under the same licence.

**v5's distances between ports** come from NGA Pub. 151, *Distances Between Ports* (11th edition, 2001), published by
the US National Geospatial-Intelligence Agency: a work of the United States government, on which no copyright is
claimed.

**The weather of v4 and v5 keeps its two sources' terms**, not CC BY-SA 4.0. It is in `v5_tasks`, `v5_episodes`,
`v5_references`, `v4_tasks`, `v4_episodes`, `v4_references`, the `dock-v1-eval-lines` and `dock-v1-eval-wind`
tables, `raw/dock-v1-eval-lines.jsonl` and `raw/dock-v1-eval-wind.jsonl`, `bundles/dock-v1-eval-lines/` and
`bundles/dock-v1-eval-wind/`, `references/lines.*` and `references/wind.*`, and the `runs/lines-*` and `runs/wind-*`
sweeps.

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

This dataset is independent: neither the Port de Barcelona, PortSimEnv's author, ECMWF, Meteocat, the NGA nor any
shipping line or agent named in it is affiliated with it or endorses it.
