# The model board: twelve models on the live, marine and wind ports

Between 7 and 9 October 2026 twelve models played every week of the live port (v2), the marine port (v3) and the
wind port (v4) once each: 15 weeks a version, 540 runs. Every run is in the dataset
[earakely-scale/PortSimEnv-AgentEnv](https://huggingface.co/datasets/earakely-scale/PortSimEnv-AgentEnv)
(`v2_episodes` to `v4_episodes`; the board as the `results` table and `results/v2.json` to `results/v4.json`) and
replays in the [Space](https://huggingface.co/spaces/earakely-scale/PortSimEnv-AgentEnv). The sweep reports, which
count every attempt, are [wind.md](wind.md), [marine.md](marine.md) and [live.md](live.md).

**Not comparable with PortSimEnv's v1 eval** ([FineEnvs/PortSimEnv-Eval](https://huggingface.co/spaces/FineEnvs/PortSimEnv-Eval)).
These are new environments, played another way: the agent re-plans the week as it unfolds, with four tools
(`get_situation`, `check_plan`, `confirm_berths`, `advance`), at most 3 planning calls a watch and 47 turns a week (52
on the wind port), where v1 plans the whole week in one go with 12 turns, 10 checks and one `submit_plan`. Each version
plays 15 weeks drawn from the one-week standard and busy eval weeks on which a rolling re-planner reaches the optimum,
where v1's eval plays 50 weeks across four tiers. Rankings don't carry over either: on v1, GLM-5.3-Flash scores above
GLM-5.3; here it scores below. The plugin's like-for-like v1 check is in [parity.md](parity.md).

## Summary

Mean reward on each version and over all 45 weeks (each week weighs the same), best first:

| Model | Provider | v4, the wind port | v3, the marine port | v2, the live port | All 45 weeks | Feasible weeks |
|---|---|---:|---:|---:|---:|---:|
| GPT-6 Astra | Azure OpenAI | 0.896 | 0.956 | 0.984 | **0.945** | 44 of 45 |
| Claude Opus 5.5 | Anthropic | 0.906 | 0.951 | 0.976 | **0.944** | 45 of 45 |
| Claude Sonnet 5.5 | Anthropic | 0.888 | 0.932 | 0.904 | **0.908** | 45 of 45 |
| GPT-6.1 Sol | Azure OpenAI | 0.745 | 0.905 | 0.957 | **0.869** | 41 of 45 |
| Claude Haiku 5.5 | Anthropic | 0.583 | 0.639 | 0.694 | **0.639** | 44 of 45 |
| Qwen3.8-2.4T | Fireworks | 0.662 | 0.519 | 0.686 | **0.622** | 28 of 45 |
| DeepSeek V4.1 Flash | Fireworks | 0.480 | 0.598 | 0.754 | **0.611** | 28 of 45 |
| GLM-5.3 | Fireworks | 0.468 | 0.593 | 0.748 | **0.603** | 28 of 45 |
| GLM-5.3-Flash | Fireworks | 0.328 | 0.461 | 0.470 | **0.420** | 18 of 45 |
| Kimi K3 | Fireworks | 0.249 | 0.446 | 0.465 | **0.386** | 18 of 45 |
| GPT-6 Luna | Azure OpenAI | 0.320 | 0.287 | 0.335 | **0.314** | 36 of 45 |
| Qwen3.8-27B | Groq | 0.090 | 0.073 | 0.055 | **0.073** | 0 of 45 |

1. **Two models share the top, a third close behind.** GPT-6 Astra and Claude Opus 5.5 are level over the 45 weeks,
   their intervals overlapping in every version; Claude Sonnet 5.5 is level with them on the wind and marine weeks
   and below them on the live ones. Opus and Sonnet broke no rule in any of their 45 weeks, Astra in one.
2. **The best open models score like a small closed one, but break far more rules.** Over the 45 weeks Claude Haiku
   5.5 averages 0.639 and the three best open models, Qwen3.8-2.4T, DeepSeek V4.1 Flash and GLM-5.3, 0.603 to 0.622,
   within noise of it (DeepSeek and GLM-5.3 score above it on the live weeks, also within noise). But Haiku keeps 44
   of its 45 weeks feasible, and each of them 28. The open models break a rule in 38% to 60% of their weeks, and
   Qwen3.8-27B in every one.
3. **The wind port is the hardest.** Eight of the twelve models score lower at each step from the live port to the
   marine port to the wind port; GPT-6.1 Sol falls the most, from 0.957 to 0.745. The versions' weeks differ (the
   wind weeks reuse 11 of the marine weeks' schedules), so this is a pattern across the sets, not a paired comparison.
4. **What breaks is the schedule, not the weather.** The rule breaks are overlapping berths, more cranes than the quay
   has, ships berthed before they can arrive and ships left without a window; a wind window is broken in 6 of the
   180 wind runs.
5. **Every model checks its drafts; not every model heeds the check.** All twelve call `check_plan` several times a
   week, but how often they confirm windows straight after a check that reported problems runs from at most 5% for
   Claude Opus 5.5 to 94% or more for Qwen3.8-27B.
6. **GPT-6 Luna's plans are valid but costly:** feasible in 36 of its 45 weeks, yet 0.314 over them, because they
   cost several times the optimum: on the wind weeks its mean regret against the anchor is 861, Claude Opus 5.5's 13.
7. **The one model small enough to fine-tune cheaply never found a valid plan.** Qwen3.8-27B is 0 for 45: the
   clearest headroom on the board for training on these weeks.

## Each version

### v4, the wind port

On the same weeks the forecast-following re-planner scores 1.000, the blind one 0.237 and the naive policy 0.183.

| Model | Provider | Weeks | Mean reward (95% CI) | Standard | Busy | Reached the end | Feasible | At the anchor | Median turns | Cost per episode |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| Claude Opus 5.5 | Anthropic | 15 of 15 | **0.906** (0.845 to 0.961) | 0.926 | 0.902 | 15 | 15 | 5 | 17 | $0.94 |
| GPT-6 Astra | Azure OpenAI | 15 of 15 | **0.896** (0.780 to 0.979) | 0.923 | 0.889 | 15 | 14 | 9 | 25 | $0.95 |
| Claude Sonnet 5.5 | Anthropic | 15 of 15 | **0.888** (0.807 to 0.953) | 0.802 | 0.909 | 15 | 15 | 3 | 17 | $0.80 |
| GPT-6.1 Sol | Azure OpenAI | 15 of 15 | **0.745** (0.576 to 0.890) | 0.869 | 0.714 | 15 | 12 | 4 | 23 | $0.15 |
| Qwen3.8-2.4T | Fireworks | 15 of 15 | **0.662** (0.460 to 0.837) | 0.926 | 0.596 | 14 | 10 | 5 | 30 | $1.30 |
| Claude Haiku 5.5 | Anthropic | 15 of 15 | **0.583** (0.460 to 0.708) | 0.373 | 0.636 | 15 | 14 | 1 | 18 | $0.05 |
| DeepSeek V4.1 Flash | Fireworks | 15 of 15 | **0.480** (0.256 to 0.701) | 0.903 | 0.374 | 10 | 7 | 3 | 22 | $0.24 |
| GLM-5.3 | Fireworks | 15 of 15 | **0.468** (0.277 to 0.661) | 0.457 | 0.471 | 13 | 7 | 3 | 29 | $1.02 |
| GLM-5.3-Flash | Fireworks | 15 of 15 | **0.328** (0.209 to 0.460) | 0.309 | 0.332 | 15 | 5 | 0 | 21 | $0.09 |
| GPT-6 Luna | Azure OpenAI | 15 of 15 | **0.320** (0.220 to 0.455) | 0.261 | 0.335 | 15 | 13 | 0 | 32 | $0.03 |
| Kimi K3 | Fireworks | 15 of 15 | **0.249** (0.159 to 0.374) | 0.457 | 0.197 | 15 | 5 | 0 | 23 | $1.34 |
| Qwen3.8-27B | Groq | 15 of 15 | **0.090** (0.064 to 0.119) | 0.139 | 0.078 | 13 | 0 | 0 | 33 | $1.38 |

### v3, the marine port

On the same weeks the rolling re-planner scores 1.000 and the naive policy 0.187.

| Model | Provider | Weeks | Mean reward (95% CI) | Standard | Busy | Reached the end | Feasible | Optimal | Median turns | Cost per episode |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| GPT-6 Astra | Azure OpenAI | 15 of 15 | **0.956** (0.910 to 0.993) | 0.970 | 0.943 | 15 | 15 | 10 | 17 | $0.53 |
| Claude Opus 5.5 | Anthropic | 15 of 15 | **0.951** (0.914 to 0.983) | 0.944 | 0.957 | 15 | 15 | 8 | 11 | $0.56 |
| Claude Sonnet 5.5 | Anthropic | 15 of 15 | **0.932** (0.892 to 0.967) | 0.914 | 0.949 | 15 | 15 | 5 | 11 | $0.45 |
| GPT-6.1 Sol | Azure OpenAI | 15 of 15 | **0.905** (0.790 to 0.977) | 0.950 | 0.865 | 15 | 14 | 7 | 14 | $0.08 |
| Claude Haiku 5.5 | Anthropic | 15 of 15 | **0.639** (0.507 to 0.765) | 0.610 | 0.664 | 15 | 15 | 0 | 12 | $0.04 |
| DeepSeek V4.1 Flash | Fireworks | 15 of 15 | **0.598** (0.392 to 0.786) | 0.678 | 0.528 | 12 | 9 | 2 | 19 | $0.24 |
| GLM-5.3 | Fireworks | 15 of 15 | **0.593** (0.368 to 0.804) | 0.561 | 0.621 | 11 | 10 | 3 | 18 | $0.47 |
| Qwen3.8-2.4T | Fireworks | 15 of 15 | **0.519** (0.296 to 0.746) | 0.364 | 0.655 | 12 | 7 | 5 | 15 | $0.83 |
| GLM-5.3-Flash | Fireworks | 15 of 15 | **0.461** (0.299 to 0.652) | 0.589 | 0.349 | 15 | 6 | 3 | 14 | $0.07 |
| Kimi K3 | Fireworks | 15 of 15 | **0.446** (0.256 to 0.636) | 0.568 | 0.339 | 15 | 6 | 0 | 16 | $1.28 |
| GPT-6 Luna | Azure OpenAI | 15 of 15 | **0.287** (0.199 to 0.407) | 0.190 | 0.372 | 15 | 11 | 0 | 19 | $0.02 |
| Qwen3.8-27B | Groq | 15 of 15 | **0.073** (0.047 to 0.100) | 0.070 | 0.076 | 15 | 0 | 0 | 24 | $0.81 |

### v2, the live port

On the same weeks the rolling re-planner scores 1.000 and the naive policy 0.202.

| Model | Provider | Weeks | Mean reward (95% CI) | Standard | Busy | Reached the end | Feasible | Optimal | Median turns | Cost per episode |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| GPT-6 Astra | Azure OpenAI | 15 of 15 | **0.984** (0.965 to 0.998) | 0.981 | 0.986 | 15 | 15 | 11 | 15 | $0.40 |
| Claude Opus 5.5 | Anthropic | 15 of 15 | **0.976** (0.954 to 0.993) | 0.981 | 0.971 | 15 | 15 | 10 | 10 | $0.43 |
| GPT-6.1 Sol | Azure OpenAI | 15 of 15 | **0.957** (0.916 to 0.991) | 0.963 | 0.952 | 15 | 15 | 10 | 13 | $0.06 |
| Claude Sonnet 5.5 | Anthropic | 15 of 15 | **0.904** (0.854 to 0.945) | 0.901 | 0.906 | 15 | 15 | 2 | 8 | $0.32 |
| DeepSeek V4.1 Flash | Fireworks | 15 of 15 | **0.754** (0.573 to 0.913) | 0.895 | 0.631 | 14 | 12 | 3 | 16 | $0.14 |
| GLM-5.3 | Fireworks | 15 of 15 | **0.748** (0.563 to 0.920) | 0.856 | 0.653 | 14 | 11 | 5 | 18 | $0.44 |
| Claude Haiku 5.5 | Anthropic | 15 of 15 | **0.694** (0.550 to 0.821) | 0.652 | 0.730 | 15 | 15 | 0 | 10 | $0.03 |
| Qwen3.8-2.4T | Fireworks | 15 of 15 | **0.686** (0.484 to 0.856) | 0.603 | 0.759 | 14 | 11 | 5 | 18 | $0.83 |
| GLM-5.3-Flash | Fireworks | 15 of 15 | **0.470** (0.307 to 0.648) | 0.518 | 0.428 | 15 | 7 | 1 | 14 | $0.04 |
| Kimi K3 | Fireworks | 15 of 15 | **0.465** (0.290 to 0.654) | 0.643 | 0.308 | 15 | 7 | 2 | 14 | $1.03 |
| GPT-6 Luna | Azure OpenAI | 15 of 15 | **0.335** (0.231 to 0.466) | 0.231 | 0.426 | 15 | 12 | 1 | 18 | $0.02 |
| Qwen3.8-27B | Groq | 15 of 15 | **0.055** (0.037 to 0.077) | 0.067 | 0.045 | 15 | 0 | 0 | 21 | $0.49 |

## What breaks

Weeks whose plan broke a rule, and the two rules broken in most of them:

| Model | v4 | v3 | v2 |
|---|---|---|---|
| Claude Opus 5.5 | 0 | 0 | 0 |
| GPT-6 Astra | 1 (tugs) | 0 | 0 |
| Claude Sonnet 5.5 | 0 | 0 | 0 |
| GPT-6.1 Sol | 3 (tugs, off the quay) | 1 (pilots) | 0 |
| Qwen3.8-2.4T | 5 (crane pool, berthed before arrival) | 8 (ships left unplanned, berthed before arrival) | 4 (berthed before arrival, crane pool) |
| Claude Haiku 5.5 | 1 (berth overlap) | 0 | 0 |
| DeepSeek V4.1 Flash | 8 (ships left unplanned, crane pool) | 6 (ships left unplanned, berthed before arrival) | 3 (crane pool, berth overlap) |
| GLM-5.3 | 8 (crane pool, berthed before arrival) | 5 (ships left unplanned, berth overlap) | 4 (berthed before arrival, crane pool) |
| GLM-5.3-Flash | 10 (crane pool, berth overlap) | 9 (crane pool, berth overlap) | 8 (berth overlap, crane pool) |
| GPT-6 Luna | 2 (ships left unplanned, berth overlap) | 4 (ships left unplanned, berthed before arrival) | 3 (crane pool, berth overlap) |
| Kimi K3 | 10 (berth overlap, crane pool) | 9 (crane pool, berth overlap) | 8 (berthed before arrival, crane pool) |
| Qwen3.8-27B | 15 (crane pool, berth overlap) | 15 (berth overlap, crane pool) | 15 (berth overlap, crane pool) |

A week counts once for each rule it breaks, however many ships break it. A week with ships left without a window is
mostly one where the model stopped calling tools before the week ended; the week then runs to its end on the windows
it had confirmed.

## Checking and heeding

How often a model confirms windows straight after a `check_plan` that reported problems in its draft:

| Model | v4 | v3 | v2 |
|---|---:|---:|---:|
| Claude Opus 5.5 | 2% | 5% | 0% |
| Claude Haiku 5.5 | 12% | 8% | 4% |
| GLM-5.3 | 19% | 9% | 6% |
| Claude Sonnet 5.5 | 11% | 10% | 22% |
| Qwen3.8-2.4T | 18% | 26% | 8% |
| DeepSeek V4.1 Flash | 31% | 20% | 15% |
| GPT-6 Luna | 20% | 25% | 24% |
| GPT-6 Astra | 19% | 26% | 33% |
| GLM-5.3-Flash | 57% | 36% | 22% |
| GPT-6.1 Sol | 55% | 35% | 17% |
| Kimi K3 | 60% | 41% | 33% |
| Qwen3.8-27B | 94% | 96% | 100% |

Confirming commits only the windows about to start, so this is a habit, not a rule break in itself: GPT-6 Astra does
it in a third of its live confirms and keeps every live week feasible. It is highest for the models that break the
most rules, Qwen3.8-27B, Kimi K3 and GLM-5.3-Flash, but GPT-6.1 Sol does it often too and breaks few.

## Cost

Model spend per week at the prices pinned in the agent (LiteLLM's public price map), and each model's spend over all
its attempts on the three versions, failed ones included:

| Model | Provider | v4 | v3 | v2 | Spend recorded, all attempts |
|---|---|---:|---:|---:|---:|
| Claude Opus 5.5 | Anthropic | $0.94 | $0.56 | $0.43 | $28.95 |
| GPT-6 Astra | Azure OpenAI | $0.95 | $0.53 | $0.40 | $28.15 |
| Claude Sonnet 5.5 | Anthropic | $0.80 | $0.45 | $0.32 | $27.08 |
| GPT-6.1 Sol | Azure OpenAI | $0.15 | $0.08 | $0.06 | $4.45 |
| Qwen3.8-2.4T | Fireworks | $1.30 | $0.83 | $0.83 | $54.49 |
| Claude Haiku 5.5 | Anthropic | $0.05 | $0.04 | $0.03 | $1.77 |
| DeepSeek V4.1 Flash | Fireworks | $0.24 | $0.24 | $0.14 | $9.82 |
| GLM-5.3 | Fireworks | $1.02 | $0.47 | $0.44 | $28.93 |
| GLM-5.3-Flash | Fireworks | $0.09 | $0.07 | $0.04 | $3.09 |
| GPT-6 Luna | Azure OpenAI | $0.03 | $0.02 | $0.02 | $1.10 |
| Kimi K3 | Fireworks | $1.34 | $1.28 | $1.03 | $71.88 |
| Qwen3.8-27B | Groq | $1.38 | $0.81 | $0.49 | $43.54 |

$303.26 recorded in all, including the first two models' earlier sweeps. A request whose usage never arrived counts at
the most it could have cost, so failed attempts inflate the recorded spend. Claude Haiku 5.5 (about $0.04 a week) and
GPT-6.1 Sol (about $0.10) give the most for the money; the open models on Fireworks write long reasoning and cost as
much a week as the leaders, Kimi K3 more.

## How it was run

- **Harness:** `portsim-llm`, PortSimEnv's harness loop as an agent-env agent, with the same prompts, tools, nudges and
  limits for every model: 47 turns a week (52 on the wind port) and at most 3 planning calls a watch, 32,000 output
  tokens a reply (16,384 for Qwen3.8-27B, Groq's limit), the provider's default reasoning (effort `medium` on the
  Responses API), one run per model and week, on local Docker.
- **Routes:** all through Scale's LiteLLM proxy. Claude on Anthropic's API; GPT on the Responses API, served by Azure
  OpenAI; Kimi K3, GLM-5.3, GLM-5.3-Flash, Qwen3.8-2.4T and DeepSeek V4.1 Flash on Fireworks; Qwen3.8-27B on Groq.
  Four of the open models are those of PortSimEnv's own eval, which ran them on other providers through the Hugging
  Face router.
- **Cost caps:** each episode stops before a request that could take it past its cap, set per model from its price,
  from $1.50 (GPT-6.1 Sol) to $12 (Kimi K3 on the marine and live weeks).
- **Failures and replays:** a failed attempt (a deploy, a provider error, a lost agent) was played again from the
  start, up to three attempts. A week that used them up, or stopped at its cost cap, was played again in a sweep named
  after its own with `-2` or `-3`: Kimi K3's wind week `dock-24B-w07x1-busy-0-e09` with a $12 cap and Qwen3.8-2.4T's
  live week `dock-24B-w16x1-busy-0` with $10; Qwen3.8-27B's pilot wind week `dock-24B-w07x1-busy-0-e04`; three of
  Claude Opus 5.5's live weeks, lost when the Docker VM restarted mid-run; and Claude Sonnet 5.5's marine week
  `dock-36A-w10x1-standard-0`, unscored in its first sweep.
- **Harness fixes during the run:** eight retries on chat completions, for Groq's tokens-per-minute limit; a reply that
  fails mid-stream is sent again, up to twice, for Fireworks' dropped streams; and a tool call whose arguments aren't
  JSON goes back into the model's history as an empty object, which Fireworks requires. None changes a run whose
  requests succeed, and no run scored before them met a failure they handle.

## Caveats

- One run per model and week: the intervals, a bootstrap over the weeks, are wide, and neither the order of the top
  three nor that of the open models is settled.
- The open models ran on Fireworks and Groq, not on the providers PortSimEnv's eval used; the same weights can score
  differently on another provider.
- The weeks are simulated pressure on real data, and the wind port transplants real weather onto 2024 schedules with a
  stand-in forecast; the dataset card's
  [Limitations](https://huggingface.co/datasets/earakely-scale/PortSimEnv-AgentEnv#limitations) sets these out.
