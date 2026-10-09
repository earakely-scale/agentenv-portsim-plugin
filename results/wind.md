# PortSim wind: portsim-llm on the live weeks in real Barcelona wind

Sweeps: `wind-pilot-gpt` (openai/gpt-6.1-sol; 2 tasks, k=1, episode cap $1.5); `wind-gpt` (openai/gpt-6.1-sol; 13 tasks, k=1, episode cap $1.5); `wind-pilot-sonnet` (anthropic/claude-sonnet-5-5; 2 tasks, k=1, episode cap $3.5); `wind-sonnet` (anthropic/claude-sonnet-5-5; 13 tasks, k=1, episode cap $3.5); `wind-pilot-opus` (anthropic/claude-opus-5-5; 2 tasks, k=1, episode cap $8); `wind-opus` (anthropic/claude-opus-5-5; 13 tasks, k=1, episode cap $8); `wind-pilot-haiku` (anthropic/claude-haiku-5-5; 2 tasks, k=1, episode cap $2); `wind-haiku` (anthropic/claude-haiku-5-5; 13 tasks, k=1, episode cap $2); `wind-pilot-astra` (openai/gpt-6-astra; 2 tasks, k=1, episode cap $8); `wind-astra` (openai/gpt-6-astra; 13 tasks, k=1, episode cap $8); `wind-pilot-luna` (openai/gpt-6-luna; 2 tasks, k=1, episode cap $2); `wind-luna` (openai/gpt-6-luna; 13 tasks, k=1, episode cap $2); `wind-pilot-kimi` (fireworks_ai/kimi-k3; 2 tasks, k=1, episode cap $6); `wind-kimi` (fireworks_ai/kimi-k3; 13 tasks, k=1, episode cap $6); `wind-kimi-2` (fireworks_ai/kimi-k3; 1 tasks, k=1, episode cap $12); `wind-pilot-glm` (fireworks_ai/glm-5p3; 2 tasks, k=1, episode cap $4); `wind-glm` (fireworks_ai/glm-5p3; 13 tasks, k=1, episode cap $4); `wind-pilot-glmflash` (fireworks_ai/glm-5p3-flash; 2 tasks, k=1, episode cap $2); `wind-glmflash` (fireworks_ai/glm-5p3-flash; 13 tasks, k=1, episode cap $2); `wind-pilot-qwen2t` (fireworks_ai/qwen3p8-2p4t-a95b; 2 tasks, k=1, episode cap $5); `wind-qwen2t` (fireworks_ai/qwen3p8-2p4t-a95b; 13 tasks, k=1, episode cap $5); `wind-pilot-qwen27b` (groq/qwen/qwen3.8-27b; 2 tasks, k=1, episode cap $4); `wind-qwen27b` (groq/qwen/qwen3.8-27b; 14 tasks, k=1, episode cap $4); `wind-pilot-dsflash` (fireworks_ai/deepseek-v4p1-flash; 2 tasks, k=1, episode cap $2); `wind-dsflash` (fireworks_ai/deepseek-v4p1-flash; 13 tasks, k=1, episode cap $2).
Harness: portsim-llm. References, on the same weeks (data/wind/references.jsonl): hindsight, the CP-SAT optimum on the wind that blew; the anchor that rewards and regret are scored against, the lower of hindsight and the best cost of the rolling re-planner following the forecasts; that rolling re-planner; blind, the same without the forecasts; hold, in bust weeks, the same holding every warning; and the naive online policy.

Spend: $153.46 known; 9 attempts with no spend recorded, $30.00 at the cap. Attempts: 231, retries: 49. Unscored runs: 2 of 182.

## Per model

| Model | Tasks | Runs scored/planned | Mean reward (95% CI) | Rolling reference | Blind reference | Naive reference | Reached done per rep | Feasible | At the anchor | Mean regret vs anchor | Mean regret vs hindsight | Mean excused cost | Median turns | Tokens in/out per episode | Cached tokens per episode | Cost per episode | Spend |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| openai/gpt-6.1-sol | 15 | 15/15 | 0.745 (0.576 to 0.890) | 1.000 | 0.237 | 0.183 | 15 | 12 | 4 | 17.333 | 3.583 | 14.467 | 23 | 427.1k/4.4k | 394.1k | $0.1495 | $2.24 |
| anthropic/claude-sonnet-5-5 | 15 | 15/15 | 0.888 (0.807 to 0.953) | 1.000 | 0.237 | 0.183 | 15 | 15 | 3 | 15.733 | 3.067 | 16.667 | 17 | 839.8k/43.6k | 753.2k | $0.8031 | $13.81 |
| anthropic/claude-opus-5-5 | 15 | 15/15 | 0.906 (0.845 to 0.961) | 1.000 | 0.237 | 0.183 | 15 | 15 | 5 | 12.867 | 0.200 | 17.667 | 17 | 626.5k/20.0k | 564.5k | $0.9363 | $14.04 |
| anthropic/claude-haiku-5-5 | 15 | 15/15 | 0.583 (0.460 to 0.708) | 1.000 | 0.237 | 0.183 | 15 | 14 | 1 | 108.500 | 94.929 | 17.667 | 18 | 1117.3k/60.8k | 1013.3k | $0.0535 | $0.82 + 3 unknown |
| openai/gpt-6-astra | 15 | 15/15 | 0.896 (0.780 to 0.979) | 1.000 | 0.237 | 0.183 | 15 | 14 | 9 | 8.214 | -4.143 | 12.533 | 25 | 481.0k/3.3k | 447.5k | $0.9465 | $14.20 |
| openai/gpt-6-luna | 15 | 15/15 | 0.320 (0.220 to 0.455) | 1.000 | 0.237 | 0.183 | 15 | 13 | 0 | 861.077 | 847.769 | 8.400 | 32 | 1225.2k/30.7k | 1161.7k | $0.0333 | $0.50 + 3 unknown |
| fireworks_ai/kimi-k3 | 15 | 15/16 | 0.249 (0.159 to 0.374) | 1.000 | 0.237 | 0.183 | 15 | 5 | 0 | 205.800 | 182.800 | 7.733 | 23 | 510.2k/45.1k | 439.7k | $1.3444 | $37.26 + 3 unknown |
| fireworks_ai/glm-5p3 | 15 | 15/15 | 0.468 (0.277 to 0.661) | 1.000 | 0.237 | 0.183 | 13 | 7 | 3 | 30.429 | 22.143 | 17.667 | 29 | 654.8k/159.0k | 610.7k | $1.0193 | $15.29 |
| fireworks_ai/glm-5p3-flash | 15 | 15/15 | 0.328 (0.209 to 0.460) | 1.000 | 0.237 | 0.183 | 15 | 5 | 0 | 74.600 | 48.200 | 9.400 | 21 | 551.4k/121.6k | 471.7k | $0.0869 | $1.52 |
| fireworks_ai/qwen3p8-2p4t-a95b | 15 | 15/15 | 0.662 (0.460 to 0.837) | 1.000 | 0.237 | 0.183 | 14 | 10 | 5 | 34.400 | 21.200 | 14.667 | 30 | 798.2k/170.0k | 752.3k | $1.2996 | $25.67 |
| groq/qwen/qwen3.8-27b | 15 | 15/16 | 0.090 (0.064 to 0.119) | 1.000 | 0.237 | 0.183 | 13 | 0 | 0 | – | – | 10.933 | 33 | 1549.9k/36.1k | 0.0k | $1.3845 | $24.05 |
| fireworks_ai/deepseek-v4p1-flash | 15 | 15/15 | 0.480 (0.256 to 0.701) | 1.000 | 0.237 | 0.183 | 10 | 7 | 3 | 5.714 | -9.571 | 11.333 | 22 | 468.3k/162.0k | 430.6k | $0.2375 | $4.06 |

## Week by week

Hindsight, the anchor and the references as cost (reward); hold is played in bust weeks only.

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

### anthropic/claude-opus-5-5

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Rolling | Blind | Hold | Naive | wind-pilot-opus r1 | wind-opus r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 (0.883) | 125 (1.000) | 125 (1.000) | infeasible (0.176) | – | 663 (0.202) | – | 0.733 | 0.733 | 22 | 36 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 226 (1.000) | 226 (1.000) | 226 (1.000) | 226 (1.000) | 242 (0.845) | infeasible (0.165) | 0.989 | – | 0.989 | 1 | 1 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 231 (1.000) | 231 (1.000) | 231 (1.000) | infeasible (0.188) | – | infeasible (0.165) | – | 0.950 | 0.950 | 5 | 5 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 239 (0.921) | 231 (1.000) | 231 (1.000) | infeasible (0.176) | – | 728 (0.201) | – | 0.771 | 0.771 | 18 | 26 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 1998 (0.980) | 1981 (1.000) | 1981 (1.000) | infeasible (0.163) | – | infeasible (0.188) | – | 0.977 | 0.977 | 3 | 20 |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1467 (1.000) | 1467 (1.000) | 1467 (1.000) | infeasible (0.171) | – | 4257 (0.200) | – | 0.936 | 0.936 | 26 | 26 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 359 (0.396) | 252 (1.000) | 252 (1.000) | infeasible (0.187) | – | 799 (0.201) | 0.791 | – | 0.791 | -84 | 23 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.184) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.176) | – | 0.672 | 0.672 | 37 | 37 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 14 (1.000) | 14 (1.000) | 14 (1.000) | infeasible (0.192) | – | 597 (0.200) | – | 0.986 | 0.986 | 1 | 1 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 206 (0.584) | 162 (1.000) | 162 (1.000) | infeasible (0.171) | – | infeasible (0.179) | – | 0.793 | 0.793 | -26 | 18 |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 10 (1.000) | 10 (1.000) | 10 (1.000) | infeasible (0.189) | – | infeasible (0.179) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 (1.000) | 113 (1.000) | 113 (1.000) | infeasible (0.174) | – | infeasible (0.183) | – | 1.000 | 1.000 | 0 | 0 |

### anthropic/claude-haiku-5-5

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Rolling | Blind | Hold | Naive | wind-pilot-haiku r1 | wind-haiku r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 (0.883) | 125 (1.000) | 125 (1.000) | infeasible (0.176) | – | 663 (0.202) | – | 0.597 | 0.597 | 48 | 62 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 226 (1.000) | 226 (1.000) | 226 (1.000) | 226 (1.000) | 242 (0.845) | infeasible (0.165) | 0.631 | – | 0.631 | 46 | 46 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 231 (1.000) | 231 (1.000) | 231 (1.000) | infeasible (0.188) | – | infeasible (0.165) | – | 0.894 | 0.894 | 11 | 11 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 239 (0.921) | 231 (1.000) | 231 (1.000) | infeasible (0.176) | – | 728 (0.201) | – | 0.735 | 0.735 | 23 | 31 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 1998 (0.980) | 1981 (1.000) | 1981 (1.000) | infeasible (0.163) | – | infeasible (0.188) | – | 0.934 | 0.934 | 41 | 58 |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1467 (1.000) | 1467 (1.000) | 1467 (1.000) | infeasible (0.171) | – | 4257 (0.200) | – | 0.265 | 0.265 | 777 | 777 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 359 (0.396) | 252 (1.000) | 252 (1.000) | infeasible (0.187) | – | 799 (0.201) | 0.490 | – | 0.490 | -30 | 77 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 0.659 | 0.659 | 38 | 38 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 0.824 | 0.824 | 17 | 17 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.184) | – | 0.298 | 0.298 | 147 | 147 |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.176) | – | 0.346 | 0.346 | 119 | 119 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 14 (1.000) | 14 (1.000) | 14 (1.000) | infeasible (0.192) | – | 597 (0.200) | – | 0.183 | 0.183 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 206 (0.584) | 162 (1.000) | 162 (1.000) | infeasible (0.171) | – | infeasible (0.179) | – | 0.445 | 0.445 | 27 | 71 |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 10 (1.000) | 10 (1.000) | 10 (1.000) | infeasible (0.189) | – | infeasible (0.179) | – | 0.445 | 0.445 | 65 | 65 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 (1.000) | 113 (1.000) | 113 (1.000) | infeasible (0.174) | – | infeasible (0.183) | – | 1.000 | 1.000 | 0 | 0 |

### openai/gpt-6-astra

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Rolling | Blind | Hold | Naive | wind-pilot-astra r1 | wind-astra r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 (0.883) | 125 (1.000) | 125 (1.000) | infeasible (0.176) | – | 663 (0.202) | – | 1.000 | 1.000 | -14 | 0 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 226 (1.000) | 226 (1.000) | 226 (1.000) | 226 (1.000) | 242 (0.845) | infeasible (0.165) | 1.000 | – | 1.000 | 0 | 0 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 231 (1.000) | 231 (1.000) | 231 (1.000) | infeasible (0.188) | – | infeasible (0.165) | – | 1.000 | 1.000 | 0 | 0 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 239 (0.921) | 231 (1.000) | 231 (1.000) | infeasible (0.176) | – | 728 (0.201) | – | 1.000 | 1.000 | -8 | 0 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 1998 (0.980) | 1981 (1.000) | 1981 (1.000) | infeasible (0.163) | – | infeasible (0.188) | – | 0.163 | 0.163 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1467 (1.000) | 1467 (1.000) | 1467 (1.000) | infeasible (0.171) | – | 4257 (0.200) | – | 0.866 | 0.866 | 57 | 57 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 359 (0.396) | 252 (1.000) | 252 (1.000) | infeasible (0.187) | – | 799 (0.201) | 0.783 | – | 0.783 | -83 | 24 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.184) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.176) | – | 0.846 | 0.846 | 15 | 15 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 14 (1.000) | 14 (1.000) | 14 (1.000) | infeasible (0.192) | – | 597 (0.200) | – | 0.986 | 0.986 | 1 | 1 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 206 (0.584) | 162 (1.000) | 162 (1.000) | infeasible (0.171) | – | infeasible (0.179) | – | 0.793 | 0.793 | -26 | 18 |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 10 (1.000) | 10 (1.000) | 10 (1.000) | infeasible (0.189) | – | infeasible (0.179) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 (1.000) | 113 (1.000) | 113 (1.000) | infeasible (0.174) | – | infeasible (0.183) | – | 1.000 | 1.000 | 0 | 0 |

### openai/gpt-6-luna

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Rolling | Blind | Hold | Naive | wind-pilot-luna r1 | wind-luna r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 (0.883) | 125 (1.000) | 125 (1.000) | infeasible (0.176) | – | 663 (0.202) | – | 0.875 | 0.875 | 1 | 15 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 226 (1.000) | 226 (1.000) | 226 (1.000) | 226 (1.000) | 242 (0.845) | infeasible (0.165) | 0.225 | – | 0.225 | 258 | 258 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 231 (1.000) | 231 (1.000) | 231 (1.000) | infeasible (0.188) | – | infeasible (0.165) | – | 0.200 | 0.200 | 1418 | 1418 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 239 (0.921) | 231 (1.000) | 231 (1.000) | infeasible (0.176) | – | 728 (0.201) | – | 0.323 | 0.323 | 136 | 144 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 1998 (0.980) | 1981 (1.000) | 1981 (1.000) | infeasible (0.163) | – | infeasible (0.188) | – | 0.188 | 0.188 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1467 (1.000) | 1467 (1.000) | 1467 (1.000) | infeasible (0.171) | – | 4257 (0.200) | – | 0.292 | 0.292 | 671 | 671 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 359 (0.396) | 252 (1.000) | 252 (1.000) | infeasible (0.187) | – | 799 (0.201) | 0.334 | – | 0.334 | 29 | 136 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 0.200 | 0.200 | 2382 | 2382 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 0.922 | 0.922 | 7 | 7 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.184) | – | 0.212 | 0.212 | 294 | 294 |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.176) | – | 0.200 | 0.200 | 735 | 735 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 14 (1.000) | 14 (1.000) | 14 (1.000) | infeasible (0.192) | – | 597 (0.200) | – | 0.249 | 0.249 | 159 | 159 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 206 (0.584) | 162 (1.000) | 162 (1.000) | infeasible (0.171) | – | infeasible (0.179) | – | 0.200 | 0.200 | 4471 | 4515 |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 10 (1.000) | 10 (1.000) | 10 (1.000) | infeasible (0.189) | – | infeasible (0.179) | – | 0.200 | 0.200 | 460 | 460 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 (1.000) | 113 (1.000) | 113 (1.000) | infeasible (0.174) | – | infeasible (0.183) | – | 0.183 | 0.183 | – | – |

### fireworks_ai/kimi-k3

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Rolling | Blind | Hold | Naive | wind-pilot-kimi r1 | wind-kimi r1 | wind-kimi-2 r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 (0.883) | 125 (1.000) | 125 (1.000) | infeasible (0.176) | – | 663 (0.202) | – | 0.153 | – | 0.153 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 226 (1.000) | 226 (1.000) | 226 (1.000) | 226 (1.000) | 242 (0.845) | infeasible (0.165) | 0.297 | – | – | 0.297 | 157 | 157 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 231 (1.000) | 231 (1.000) | 231 (1.000) | infeasible (0.188) | – | infeasible (0.165) | – | 0.129 | – | 0.129 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 239 (0.921) | 231 (1.000) | 231 (1.000) | infeasible (0.176) | – | 728 (0.201) | – | – | 0.430 | 0.430 | 88 | 96 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 1998 (0.980) | 1981 (1.000) | 1981 (1.000) | infeasible (0.163) | – | infeasible (0.188) | – | 0.100 | – | 0.100 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1467 (1.000) | 1467 (1.000) | 1467 (1.000) | infeasible (0.171) | – | 4257 (0.200) | – | 0.409 | – | 0.409 | 416 | 416 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 359 (0.396) | 252 (1.000) | 252 (1.000) | infeasible (0.187) | – | 799 (0.201) | 0.207 | – | – | 0.207 | 252 | 359 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 0.170 | – | 0.170 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 0.148 | – | 0.148 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.184) | – | 0.104 | – | 0.104 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.176) | – | 0.080 | – | 0.080 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 14 (1.000) | 14 (1.000) | 14 (1.000) | infeasible (0.192) | – | 597 (0.200) | – | 0.986 | – | 0.986 | 1 | 1 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 206 (0.584) | 162 (1.000) | 162 (1.000) | infeasible (0.171) | – | infeasible (0.179) | – | 0.164 | – | 0.164 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 10 (1.000) | 10 (1.000) | 10 (1.000) | infeasible (0.189) | – | infeasible (0.179) | – | 0.179 | – | 0.179 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 (1.000) | 113 (1.000) | 113 (1.000) | infeasible (0.174) | – | infeasible (0.183) | – | 0.174 | – | 0.174 | – | – |

### fireworks_ai/glm-5p3

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Rolling | Blind | Hold | Naive | wind-pilot-glm r1 | wind-glm r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 (0.883) | 125 (1.000) | 125 (1.000) | infeasible (0.176) | – | 663 (0.202) | – | 0.307 | 0.307 | 164 | 178 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 226 (1.000) | 226 (1.000) | 226 (1.000) | 226 (1.000) | 242 (0.845) | infeasible (0.165) | 0.900 | – | 0.900 | 10 | 10 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 231 (1.000) | 231 (1.000) | 231 (1.000) | infeasible (0.188) | – | infeasible (0.165) | – | 1.000 | 1.000 | 0 | 0 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 239 (0.921) | 231 (1.000) | 231 (1.000) | infeasible (0.176) | – | 728 (0.201) | – | 0.188 | 0.188 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 1998 (0.980) | 1981 (1.000) | 1981 (1.000) | infeasible (0.163) | – | infeasible (0.188) | – | 0.175 | 0.175 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1467 (1.000) | 1467 (1.000) | 1467 (1.000) | infeasible (0.171) | – | 4257 (0.200) | – | 0.000 | 0.000 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 359 (0.396) | 252 (1.000) | 252 (1.000) | infeasible (0.187) | – | 799 (0.201) | 0.187 | – | 0.187 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 0.170 | 0.170 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.184) | – | 0.128 | 0.128 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.176) | – | 0.104 | 0.104 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 14 (1.000) | 14 (1.000) | 14 (1.000) | infeasible (0.192) | – | 597 (0.200) | – | 0.183 | 0.183 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 206 (0.584) | 162 (1.000) | 162 (1.000) | infeasible (0.171) | – | infeasible (0.179) | – | 0.844 | 0.844 | -31 | 13 |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 10 (1.000) | 10 (1.000) | 10 (1.000) | infeasible (0.189) | – | infeasible (0.179) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 (1.000) | 113 (1.000) | 113 (1.000) | infeasible (0.174) | – | infeasible (0.183) | – | 0.837 | 0.837 | 12 | 12 |

### fireworks_ai/glm-5p3-flash

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Rolling | Blind | Hold | Naive | wind-pilot-glmflash r1 | wind-glmflash r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 (0.883) | 125 (1.000) | 125 (1.000) | infeasible (0.176) | – | 663 (0.202) | – | 0.141 | 0.141 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 226 (1.000) | 226 (1.000) | 226 (1.000) | 226 (1.000) | 242 (0.845) | infeasible (0.165) | 0.700 | – | 0.700 | 35 | 35 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 231 (1.000) | 231 (1.000) | 231 (1.000) | infeasible (0.188) | – | infeasible (0.165) | – | 0.141 | 0.141 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 239 (0.921) | 231 (1.000) | 231 (1.000) | infeasible (0.176) | – | 728 (0.201) | – | 0.597 | 0.597 | 46 | 54 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 1998 (0.980) | 1981 (1.000) | 1981 (1.000) | infeasible (0.163) | – | infeasible (0.188) | – | 0.789 | 0.789 | 189 | 206 |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1467 (1.000) | 1467 (1.000) | 1467 (1.000) | infeasible (0.171) | – | 4257 (0.200) | – | 0.143 | 0.143 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 359 (0.396) | 252 (1.000) | 252 (1.000) | infeasible (0.187) | – | 799 (0.201) | 0.593 | – | 0.593 | -53 | 54 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 0.126 | 0.126 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 0.185 | 0.185 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.184) | – | 0.168 | 0.168 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.176) | – | 0.184 | 0.184 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 14 (1.000) | 14 (1.000) | 14 (1.000) | infeasible (0.192) | – | 597 (0.200) | – | 0.167 | 0.167 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 206 (0.584) | 162 (1.000) | 162 (1.000) | infeasible (0.171) | – | infeasible (0.179) | – | 0.107 | 0.107 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 10 (1.000) | 10 (1.000) | 10 (1.000) | infeasible (0.189) | – | infeasible (0.179) | – | 0.168 | 0.168 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 (1.000) | 113 (1.000) | 113 (1.000) | infeasible (0.174) | – | infeasible (0.183) | – | 0.706 | 0.706 | 24 | 24 |

### fireworks_ai/qwen3p8-2p4t-a95b

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Rolling | Blind | Hold | Naive | wind-pilot-qwen2t r1 | wind-qwen2t r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 (0.883) | 125 (1.000) | 125 (1.000) | infeasible (0.176) | – | 663 (0.202) | – | 0.188 | 0.188 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 226 (1.000) | 226 (1.000) | 226 (1.000) | 226 (1.000) | 242 (0.845) | infeasible (0.165) | 1.000 | – | 1.000 | 0 | 0 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 231 (1.000) | 231 (1.000) | 231 (1.000) | infeasible (0.188) | – | infeasible (0.165) | – | 0.176 | 0.176 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 239 (0.921) | 231 (1.000) | 231 (1.000) | infeasible (0.176) | – | 728 (0.201) | – | 0.771 | 0.771 | 18 | 26 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 1998 (0.980) | 1981 (1.000) | 1981 (1.000) | infeasible (0.163) | – | infeasible (0.188) | – | 0.720 | 0.720 | 272 | 289 |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1467 (1.000) | 1467 (1.000) | 1467 (1.000) | infeasible (0.171) | – | 4257 (0.200) | – | 0.000 | 0.000 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 359 (0.396) | 252 (1.000) | 252 (1.000) | infeasible (0.187) | – | 799 (0.201) | 0.791 | – | 0.791 | -84 | 23 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.184) | – | 0.168 | 0.168 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.176) | – | 0.945 | 0.945 | 5 | 5 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 14 (1.000) | 14 (1.000) | 14 (1.000) | infeasible (0.192) | – | 597 (0.200) | – | 0.986 | 0.986 | 1 | 1 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 206 (0.584) | 162 (1.000) | 162 (1.000) | infeasible (0.171) | – | infeasible (0.179) | – | 0.179 | 0.179 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 10 (1.000) | 10 (1.000) | 10 (1.000) | infeasible (0.189) | – | infeasible (0.179) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 (1.000) | 113 (1.000) | 113 (1.000) | infeasible (0.174) | – | infeasible (0.183) | – | 1.000 | 1.000 | 0 | 0 |

### groq/qwen/qwen3.8-27b

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Rolling | Blind | Hold | Naive | wind-pilot-qwen27b r1 | wind-qwen27b r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 (0.883) | 125 (1.000) | 125 (1.000) | infeasible (0.176) | – | 663 (0.202) | – | 0.094 | 0.094 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 226 (1.000) | 226 (1.000) | 226 (1.000) | 226 (1.000) | 242 (0.845) | infeasible (0.165) | – | 0.071 | 0.071 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 231 (1.000) | 231 (1.000) | 231 (1.000) | infeasible (0.188) | – | infeasible (0.165) | – | 0.082 | 0.082 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 239 (0.921) | 231 (1.000) | 231 (1.000) | infeasible (0.176) | – | 728 (0.201) | – | 0.165 | 0.165 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 1998 (0.980) | 1981 (1.000) | 1981 (1.000) | infeasible (0.163) | – | infeasible (0.188) | – | 0.025 | 0.025 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1467 (1.000) | 1467 (1.000) | 1467 (1.000) | infeasible (0.171) | – | 4257 (0.200) | – | 0.071 | 0.071 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 359 (0.396) | 252 (1.000) | 252 (1.000) | infeasible (0.187) | – | 799 (0.201) | 0.093 | – | 0.093 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 0.119 | 0.119 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 0.170 | 0.170 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.184) | – | 0.024 | 0.024 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.176) | – | 0.008 | 0.008 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 14 (1.000) | 14 (1.000) | 14 (1.000) | infeasible (0.192) | – | 597 (0.200) | – | 0.167 | 0.167 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 206 (0.584) | 162 (1.000) | 162 (1.000) | infeasible (0.171) | – | infeasible (0.179) | – | 0.021 | 0.021 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 10 (1.000) | 10 (1.000) | 10 (1.000) | infeasible (0.189) | – | infeasible (0.179) | – | 0.158 | 0.158 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 (1.000) | 113 (1.000) | 113 (1.000) | infeasible (0.174) | – | infeasible (0.183) | – | 0.087 | 0.087 | – | – |

### fireworks_ai/deepseek-v4p1-flash

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Rolling | Blind | Hold | Naive | wind-pilot-dsflash r1 | wind-dsflash r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 (0.883) | 125 (1.000) | 125 (1.000) | infeasible (0.176) | – | 663 (0.202) | – | 0.153 | 0.153 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 226 (1.000) | 226 (1.000) | 226 (1.000) | 226 (1.000) | 242 (0.845) | infeasible (0.165) | 0.000 | – | 0.000 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 231 (1.000) | 231 (1.000) | 231 (1.000) | infeasible (0.188) | – | infeasible (0.165) | – | 0.894 | 0.894 | 11 | 11 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 239 (0.921) | 231 (1.000) | 231 (1.000) | infeasible (0.176) | – | 728 (0.201) | – | 0.188 | 0.188 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 1998 (0.980) | 1981 (1.000) | 1981 (1.000) | infeasible (0.163) | – | infeasible (0.188) | – | 0.000 | 0.000 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1467 (1.000) | 1467 (1.000) | 1467 (1.000) | infeasible (0.171) | – | 4257 (0.200) | – | 0.000 | 0.000 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 359 (0.396) | 252 (1.000) | 252 (1.000) | infeasible (0.187) | – | 799 (0.201) | 0.791 | – | 0.791 | -84 | 23 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 406 (1.000) | 406 (1.000) | 406 (1.000) | infeasible (0.193) | – | infeasible (0.163) | – | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.184) | – | 0.152 | 0.152 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 (1.000) | 40 (1.000) | 40 (1.000) | infeasible (0.192) | – | infeasible (0.176) | – | 0.104 | 0.104 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 14 (1.000) | 14 (1.000) | 14 (1.000) | infeasible (0.192) | – | 597 (0.200) | – | 0.986 | 0.986 | 1 | 1 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 206 (0.584) | 162 (1.000) | 162 (1.000) | infeasible (0.171) | – | infeasible (0.179) | – | 0.000 | 0.000 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 10 (1.000) | 10 (1.000) | 10 (1.000) | infeasible (0.189) | – | infeasible (0.179) | – | 0.930 | 0.930 | 5 | 5 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 (1.000) | 113 (1.000) | 113 (1.000) | infeasible (0.174) | – | infeasible (0.183) | – | 1.000 | 1.000 | 0 | 0 |

## Unscored runs

| Sweep | Model | Task | Rep | Attempts | Last outcome | Spend |
|---|---|---|---:|---:|---|---:|
| wind-kimi | fireworks_ai/kimi-k3 | dock-24B-w07x1-busy-0-e09 | 1 | 3 | cost_cap | $6.12 |
| wind-pilot-qwen27b | groq/qwen/qwen3.8-27b | dock-24B-w07x1-busy-0-e04 | 1 | 3 | provider_error | $3.28 |

## Runs whose agent reward differs from the verifier's

Only runs whose agent saw the week end.

None.
