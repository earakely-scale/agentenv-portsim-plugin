# PortSim wind: portsim-llm on the live weeks in real Barcelona wind

Sweeps: `wind-pilot-sonnet` (anthropic/claude-sonnet-5-5; 2 tasks, k=1, episode cap $3.5); `wind-pilot-gpt` (openai/gpt-6.1-sol; 2 tasks, k=1, episode cap $1.5); `wind-sonnet` (anthropic/claude-sonnet-5-5; 13 tasks, k=1, episode cap $3.5); `wind-gpt` (openai/gpt-6.1-sol; 13 tasks, k=1, episode cap $1.5).
Harness: portsim-llm. References, on the same weeks (data/wind/references.jsonl): hindsight, the CP-SAT optimum on the wind that blew; the anchor that rewards and regret are scored against, the lower of hindsight and the best cost of the rolling re-planner following the forecasts; that rolling re-planner; blind, the same without the forecasts; hold, in bust weeks, the same holding every warning; and the naive online policy.

Spend: $16.05 known; 0 attempts with no spend recorded, $0.00 at the cap. Attempts: 32, retries: 2. Unscored runs: 0 of 30.

## Per model

| Model | Tasks | Runs scored/planned | Mean reward (95% CI) | Rolling reference | Blind reference | Naive reference | Reached done per rep | Feasible | At the anchor | Mean regret vs anchor | Mean regret vs hindsight | Mean excused cost | Median turns | Tokens in/out per episode | Cached tokens per episode | Cost per episode | Spend |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| anthropic/claude-sonnet-5-5 | 15 | 15/15 | 0.888 (0.807 to 0.953) | 1.000 | 0.237 | 0.183 | 15 | 15 | 3 | 15.733 | 3.067 | 16.667 | 17 | 839.8k/43.6k | 753.2k | $0.8031 | $13.81 |
| openai/gpt-6.1-sol | 15 | 15/15 | 0.745 (0.576 to 0.890) | 1.000 | 0.237 | 0.183 | 15 | 12 | 4 | 17.333 | 3.583 | 14.467 | 23 | 427.1k/4.4k | 394.1k | $0.1495 | $2.24 |

## Week by week

Hindsight, the anchor and the references as cost (reward); hold is played in bust weeks only.

### anthropic/claude-sonnet-5-5

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Rolling | Blind | Hold | Naive | wind-pilot-sonnet r1 | wind-sonnet r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 (0.883) | 125 (1.000) | 125 (1.000) | infeasible (0.176) | – | 663 (0.202) | – | 1.000 | 1.000 | -14 | 0 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 226 (1.000) | 226 (1.000) | 226 (1.000) | 226 (1.000) | 242 (0.845) | infeasible (0.165) | 0.989 | – | 0.989 | 1 | 1 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 231 (1.000) | 231 (1.000) | 231 (1.000) | infeasible (0.188) | – | infeasible (0.165) | – | 0.894 | 0.894 | 11 | 11 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 239 (0.921) | 231 (1.000) | 231 (1.000) | infeasible (0.176) | – | 728 (0.201) | – | 0.771 | 0.771 | 18 | 26 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 1998 (0.980) | 1981 (1.000) | 1981 (1.000) | infeasible (0.163) | – | infeasible (0.188) | – | 0.994 | 0.994 | -12 | 5 |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1467 (1.000) | 1467 (1.000) | 1467 (1.000) | infeasible (0.171) | – | 4257 (0.200) | – | 0.901 | 0.901 | 41 | 41 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 359 (0.396) | 252 (1.000) | 252 (1.000) | infeasible (0.187) | – | 799 (0.201) | 0.490 | – | 0.490 | -30 | 77 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 0.922 | 0.922 | 7 | 7 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.184) | – | 0.894 | 0.894 | 10 | 10 |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.176) | – | 0.609 | 0.609 | 47 | 47 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 14 (1.000) | 14 (1.000) | 14 (1.000) | infeasible (0.192) | – | 597 (0.200) | – | 0.986 | 0.986 | 1 | 1 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 206 (0.584) | 162 (1.000) | 162 (1.000) | infeasible (0.171) | – | infeasible (0.179) | – | 0.936 | 0.936 | -39 | 5 |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 10 (1.000) | 10 (1.000) | 10 (1.000) | infeasible (0.189) | – | infeasible (0.179) | – | 0.930 | 0.930 | 5 | 5 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 (1.000) | 113 (1.000) | 113 (1.000) | infeasible (0.174) | – | infeasible (0.183) | – | 1.000 | 1.000 | 0 | 0 |

### openai/gpt-6.1-sol

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Rolling | Blind | Hold | Naive | wind-pilot-gpt r1 | wind-gpt r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 (0.883) | 125 (1.000) | 125 (1.000) | infeasible (0.176) | – | 663 (0.202) | – | 1.000 | 1.000 | -14 | 0 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 226 (1.000) | 226 (1.000) | 226 (1.000) | 226 (1.000) | 242 (0.845) | infeasible (0.165) | 0.989 | – | 0.989 | 1 | 1 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 231 (1.000) | 231 (1.000) | 231 (1.000) | infeasible (0.188) | – | infeasible (0.165) | – | 0.188 | 0.188 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 239 (0.921) | 231 (1.000) | 231 (1.000) | infeasible (0.176) | – | 728 (0.201) | – | 0.188 | 0.188 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 1998 (0.980) | 1981 (1.000) | 1981 (1.000) | infeasible (0.163) | – | infeasible (0.188) | – | 0.163 | 0.163 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1467 (1.000) | 1467 (1.000) | 1467 (1.000) | infeasible (0.171) | – | 4257 (0.200) | – | 0.828 | 0.828 | 75 | 75 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 359 (0.396) | 252 (1.000) | 252 (1.000) | infeasible (0.187) | – | 799 (0.201) | 0.620 | – | 0.620 | -58 | 49 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 0.944 | 0.944 | 5 | 5 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.184) | – | 0.945 | 0.945 | 5 | 5 |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.176) | – | 0.721 | 0.721 | 30 | 30 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 14 (1.000) | 14 (1.000) | 14 (1.000) | infeasible (0.192) | – | 597 (0.200) | – | 0.986 | 0.986 | 1 | 1 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 206 (0.584) | 162 (1.000) | 162 (1.000) | infeasible (0.171) | – | infeasible (0.179) | – | 0.597 | 0.597 | -2 | 42 |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 10 (1.000) | 10 (1.000) | 10 (1.000) | infeasible (0.189) | – | infeasible (0.179) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 (1.000) | 113 (1.000) | 113 (1.000) | infeasible (0.174) | – | infeasible (0.183) | – | 1.000 | 1.000 | 0 | 0 |

## Unscored runs

None.

## Runs whose agent reward differs from the verifier's

Only runs whose agent saw the week end.

None.
