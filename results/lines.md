# PortSim lines: portsim-llm on the wind weeks with the ships' agents

Sweeps: `lines-fix6-astra` (openai/gpt-6-astra; 15 tasks, k=1, episode cap $15); `lines-r6-dsflash` (fireworks_ai/deepseek-v4p1-flash; 15 tasks, k=1, episode cap $3); `lines-r6-dsflash-b` (fireworks_ai/deepseek-v4p1-flash; 3 tasks, k=1, episode cap $3); `lines-r6-dsflash-c` (fireworks_ai/deepseek-v4p1-flash; 3 tasks, k=1, episode cap $3); `lines-r6-dsflash-d` (fireworks_ai/deepseek-v4p1-flash; 2 tasks, k=1, episode cap $3); `lines-r6-glm` (fireworks_ai/glm-5p3; 15 tasks, k=1, episode cap $10); `lines-r6-glm-b` (fireworks_ai/glm-5p3; 5 tasks, k=1, episode cap $10); `lines-r6-glm-c` (fireworks_ai/glm-5p3; 4 tasks, k=1, episode cap $10); `lines-r6-glm-d` (fireworks_ai/glm-5p3; 4 tasks, k=1, episode cap $10); `lines-r6-glm-e` (fireworks_ai/glm-5p3; 2 tasks, k=1, episode cap $10); `lines-r6-glm-f` (fireworks_ai/glm-5p3; 2 tasks, k=1, episode cap $10); `lines-r6-glm-g` (fireworks_ai/glm-5p3; 1 tasks, k=1, episode cap $10); `lines-r6-glm-h` (fireworks_ai/glm-5p3; 1 tasks, k=1, episode cap $10); `lines-r6-glm-i` (fireworks_ai/glm-5p3; 1 tasks, k=1, episode cap $10); `lines-r6-glm-j` (fireworks_ai/glm-5p3; 1 tasks, k=1, episode cap $10); `lines-r6-glmflash` (fireworks_ai/glm-5p3-flash; 15 tasks, k=1, episode cap $1); `lines-r6-glmflash-b` (fireworks_ai/glm-5p3-flash; 4 tasks, k=1, episode cap $1); `lines-r6-glmflash-c` (fireworks_ai/glm-5p3-flash; 4 tasks, k=1, episode cap $1); `lines-r6-glmflash-d` (fireworks_ai/glm-5p3-flash; 3 tasks, k=1, episode cap $1); `lines-r6-glmflash-e` (fireworks_ai/glm-5p3-flash; 1 tasks, k=1, episode cap $1); `lines-r6-glmflash-f` (fireworks_ai/glm-5p3-flash; 1 tasks, k=1, episode cap $1); `lines-r6-glmflash-g` (fireworks_ai/glm-5p3-flash; 1 tasks, k=1, episode cap $1); `lines-r6-gpt` (openai/gpt-6.1-sol; 15 tasks, k=1, episode cap $3); `lines-r6-haiku` (anthropic/claude-haiku-5-5; 15 tasks, k=1, episode cap $1); `lines-r6-kimi` (fireworks_ai/kimi-k3; 15 tasks, k=1, episode cap $10); `lines-r6-kimi-b` (fireworks_ai/kimi-k3; 4 tasks, k=1, episode cap $10); `lines-r6-kimi-c` (fireworks_ai/kimi-k3; 3 tasks, k=1, episode cap $10); `lines-r6-kimi-d` (fireworks_ai/kimi-k3; 3 tasks, k=1, episode cap $10); `lines-r6-luna` (openai/gpt-6-luna; 15 tasks, k=1, episode cap $1); `lines-r6-opus` (anthropic/claude-opus-5-5; 15 tasks, k=1, episode cap $15); `lines-r6-qwen27b` (groq/qwen/qwen3.8-27b; 15 tasks, k=1, episode cap $10); `lines-r6-qwen2t` (fireworks_ai/qwen3p8-2p4t-a95b; 15 tasks, k=1, episode cap $10); `lines-r6-qwen2t-b` (fireworks_ai/qwen3p8-2p4t-a95b; 4 tasks, k=1, episode cap $10); `lines-r6-qwen2t-c` (fireworks_ai/qwen3p8-2p4t-a95b; 4 tasks, k=1, episode cap $10); `lines-r6-qwen2t-d` (fireworks_ai/qwen3p8-2p4t-a95b; 4 tasks, k=1, episode cap $10); `lines-r6-qwen2t-e` (fireworks_ai/qwen3p8-2p4t-a95b; 1 tasks, k=1, episode cap $10); `lines-r6-qwen2t-f` (fireworks_ai/qwen3p8-2p4t-a95b; 1 tasks, k=1, episode cap $10); `lines-r6-sonnet` (anthropic/claude-sonnet-5-5; 15 tasks, k=1, episode cap $10).
Harness: portsim-llm, with each ship's agent a portsim-line agent it can message. References, on the same weeks (data/lines/references.jsonl): hindsight, the clairvoyant CP-SAT optimum that knows every arrival and slows ships from the first watch it could ask; the anchor that rewards and regret are scored against, the lower of that cost and the follower's best over its four solver configurations; the follower, in its first configuration, which re-plans at every watch on the arrivals as known and requests arrival times through the ships' agents; silent, the same never asking them; and the naive online policy.

Spend: $238.31 known; 31 attempts with no spend recorded, $194.00 at the cap. Attempts: 216, retries: 6. Unscored runs: 67 of 247.

## Per model

| Model | Tasks | Runs scored/planned | Mean reward (95% CI) | Follower reference | Silent reference | Naive reference | Reached done per rep | Feasible | At the anchor | Mean regret vs anchor | Mean regret vs hindsight | Mean excused cost | Mean hours at anchor | Messages per episode | Median turns | Tokens in/out per episode | Cached tokens per episode | Cost per episode | Spend |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| openai/gpt-6-astra | 15 | 15/15 | 0.568 (0.420 to 0.722) | 0.548 | 0.242 | 0.184 | 15 | 14 | 3 | 201.286 | 180.357 | 21.800 | 24.867 | 44.200 | 46 | 1369.0k/5.7k | 1313.3k | $2.1568 | $32.35 |
| fireworks_ai/deepseek-v4p1-flash | 15 | 15/23 | 0.168 (0.089 to 0.269) | 0.548 | 0.242 | 0.184 | 6 | 6 | 0 | 683.500 | 651.167 | 60.333 | 53.333 | 18.133 | 16 | 955.9k/232.2k | 893.9k | $0.3027 | $5.39 + 5 unknown |
| fireworks_ai/glm-5p3 | 15 | 15/36 | 0.153 (0.029 to 0.308) | 0.548 | 0.242 | 0.184 | 5 | 3 | 0 | 106.000 | 106.000 | 0.000 | 1.667 | 19.267 | 2 | 448.0k/135.1k | 417.4k | $0.7457 | $12.98 + 8 unknown |
| fireworks_ai/glm-5p3-flash | 15 | 15/29 | 0.261 (0.171 to 0.367) | 0.548 | 0.242 | 0.184 | 11 | 6 | 0 | 231.833 | 199.500 | 249.667 | 80.667 | 30.800 | 31 | 1289.6k/255.5k | 1140.0k | $0.1844 | $2.85 + 9 unknown |
| openai/gpt-6.1-sol | 15 | 15/15 | 0.536 (0.392 to 0.693) | 0.548 | 0.242 | 0.184 | 15 | 14 | 3 | 216.000 | 195.071 | 29.267 | 30.067 | 47.200 | 39 | 1216.6k/7.5k | 1149.9k | $0.3233 | $4.85 |
| anthropic/claude-haiku-5-5 | 15 | 15/15 | 0.258 (0.203 to 0.322) | 0.548 | 0.242 | 0.184 | 15 | 13 | 0 | 1024.846 | 1002.308 | 40.000 | 100.867 | 15.200 | 22 | 2383.2k/104.5k | 2175.3k | $0.1000 | $1.70 |
| fireworks_ai/kimi-k3 | 15 | 15/25 | 0.231 (0.172 to 0.308) | 0.548 | 0.242 | 0.184 | 15 | 5 | 0 | 627.400 | 588.600 | 63.733 | 121.533 | 36.067 | 30 | 1341.5k/81.2k | 1192.4k | $2.0224 | $37.85 + 4 unknown |
| openai/gpt-6-luna | 15 | 15/15 | 0.234 (0.199 to 0.284) | 0.548 | 0.242 | 0.184 | 15 | 13 | 0 | 2180.692 | 2158.154 | 41.733 | 186.200 | 11.000 | 34 | 2046.4k/50.5k | 1941.7k | $0.0551 | $0.85 |
| anthropic/claude-opus-5-5 | 15 | 15/15 | 0.593 (0.453 to 0.725) | 0.548 | 0.242 | 0.184 | 15 | 14 | 1 | 136.500 | 115.571 | 17.867 | 26.600 | 48.267 | 33 | 2298.8k/44.2k | 2165.3k | $2.4167 | $42.09 |
| groq/qwen/qwen3.8-27b | 15 | 15/15 | 0.143 (0.118 to 0.164) | 0.548 | 0.242 | 0.184 | 15 | 1 | 0 | 1718.000 | 1524.000 | 225.800 | 171.400 | 0.467 | 39 | 1962.2k/14.6k | 0.0k | $1.6281 | $36.35 |
| fireworks_ai/qwen3p8-2p4t-a95b | 15 | 15/29 | 0.291 (0.171 to 0.423) | 0.548 | 0.242 | 0.184 | 11 | 8 | 0 | 380.625 | 356.375 | 23.667 | 46.067 | 32.933 | 30 | 1161.2k/308.4k | 1090.4k | $2.2646 | $37.13 + 5 unknown |
| anthropic/claude-sonnet-5-5 | 15 | 15/15 | 0.387 (0.268 to 0.517) | 0.548 | 0.242 | 0.184 | 15 | 15 | 0 | 524.600 | 505.067 | 42.133 | 51.267 | 24.533 | 27 | 2140.0k/77.4k | 1986.4k | $1.5549 | $23.92 |

## Week by week

Hindsight as its cost; the anchor and the references as cost (reward).

### openai/gpt-6-astra

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 509 | 410 (1.000) | 410 (1.000) | 1554 (0.200) | 2318 (0.200) | 0.307 | 0.307 | 104 | 203 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 503 | 503 (1.000) | 613 (0.517) | 2459 (0.200) | infeasible (0.141) | 0.744 | 0.744 | 46 | 46 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 874 | 680 (1.000) | 680 (1.000) | 2941 (0.200) | infeasible (0.165) | 1.000 | 1.000 | -262 | -68 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 772 | 772 (1.000) | 793 (0.816) | 1197 (0.204) | 2658 (0.200) | 1.000 | 1.000 | -14 | -14 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4248 | 4248 (1.000) | 9538 (0.215) | 5964 (0.420) | 9572 (0.214) | 0.695 | 0.695 | 638 | 638 |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 2582 | 2582 (1.000) | 2807 (0.575) | 4588 (0.201) | infeasible (0.171) | 0.897 | 0.897 | 41 | 41 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 933 | 933 (1.000) | 1049 (0.571) | 1850 (0.202) | infeasible (0.160) | 0.386 | 0.386 | 220 | 220 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 1374 | 1374 (1.000) | 1406 (0.768) | 1550 (0.322) | infeasible (0.163) | 0.659 | 0.659 | 52 | 52 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 1676 | 1676 (1.000) | 1765 (0.468) | 2388 (0.200) | 3450 (0.200) | 0.468 | 0.468 | 89 | 89 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 1232 | 1232 (1.000) | 1618 (0.266) | 4601 (0.200) | 6441 (0.200) | 0.252 | 0.252 | 424 | 424 |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 633 | 633 (1.000) | 795 (0.354) | 3925 (0.200) | infeasible (0.184) | 0.414 | 0.414 | 130 | 130 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 924 | 924 (1.000) | 1515 (0.200) | 1879 (0.200) | 3558 (0.200) | 0.200 | 0.200 | 829 | 829 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 1437 | 1437 (1.000) | 1909 (0.218) | 4831 (0.200) | infeasible (0.179) | 0.326 | 0.326 | 228 | 228 |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 411 | 411 (1.000) | 417 (0.926) | 475 (0.483) | infeasible (0.179) | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 1093 | 1093 (1.000) | 1286 (0.319) | 1999 (0.200) | 3107 (0.200) | 0.174 | 0.174 | – | – |

### fireworks_ai/deepseek-v4p1-flash

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | lines-r6-dsflash r1 | lines-r6-dsflash-b r1 | lines-r6-dsflash-c r1 | lines-r6-dsflash-d r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 509 | 410 (1.000) | 410 (1.000) | 1554 (0.200) | 2318 (0.200) | 0.188 | – | – | – | 0.188 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 503 | 503 (1.000) | 613 (0.517) | 2459 (0.200) | infeasible (0.141) | – | – | 0.000 | – | 0.000 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 874 | 680 (1.000) | 680 (1.000) | 2941 (0.200) | infeasible (0.165) | 0.207 | – | – | – | 0.207 | 112 | 306 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 772 | 772 (1.000) | 793 (0.816) | 1197 (0.204) | 2658 (0.200) | – | – | 0.200 | – | 0.200 | 966 | 966 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4248 | 4248 (1.000) | 9538 (0.215) | 5964 (0.420) | 9572 (0.214) | – | – | – | 0.000 | 0.000 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 2582 | 2582 (1.000) | 2807 (0.575) | 4588 (0.201) | infeasible (0.171) | – | – | – | 0.157 | 0.157 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 933 | 933 (1.000) | 1049 (0.571) | 1850 (0.202) | infeasible (0.160) | 0.187 | – | – | – | 0.187 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 1374 | 1374 (1.000) | 1406 (0.768) | 1550 (0.322) | infeasible (0.163) | 0.257 | – | – | – | 0.257 | 247 | 247 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 1676 | 1676 (1.000) | 1765 (0.468) | 2388 (0.200) | 3450 (0.200) | 0.000 | – | – | – | 0.000 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 1232 | 1232 (1.000) | 1618 (0.266) | 4601 (0.200) | 6441 (0.200) | 0.000 | – | – | – | 0.000 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 633 | 633 (1.000) | 795 (0.354) | 3925 (0.200) | infeasible (0.184) | – | – | 0.184 | – | 0.184 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 924 | 924 (1.000) | 1515 (0.200) | 1879 (0.200) | 3558 (0.200) | 0.200 | – | – | – | 0.200 | 1080 | 1080 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 1437 | 1437 (1.000) | 1909 (0.218) | 4831 (0.200) | infeasible (0.179) | 0.000 | – | – | – | 0.000 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 411 | 411 (1.000) | 417 (0.926) | 475 (0.483) | infeasible (0.179) | 0.733 | – | – | – | 0.733 | 25 | 25 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 1093 | 1093 (1.000) | 1286 (0.319) | 1999 (0.200) | 3107 (0.200) | 0.200 | – | – | – | 0.200 | 1477 | 1477 |

### fireworks_ai/glm-5p3

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | lines-r6-glm r1 | lines-r6-glm-b r1 | lines-r6-glm-c r1 | lines-r6-glm-d r1 | lines-r6-glm-e r1 | lines-r6-glm-f r1 | lines-r6-glm-g r1 | lines-r6-glm-h r1 | lines-r6-glm-i r1 | lines-r6-glm-j r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 509 | 410 (1.000) | 410 (1.000) | 1554 (0.200) | 2318 (0.200) | 0.000 | – | – | – | – | – | – | – | – | – | 0.000 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 503 | 503 (1.000) | 613 (0.517) | 2459 (0.200) | infeasible (0.141) | – | – | – | 0.888 | – | – | – | – | – | – | 0.888 | 18 | 18 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 874 | 680 (1.000) | 680 (1.000) | 2941 (0.200) | infeasible (0.165) | – | – | – | – | – | – | – | – | – | 0.000 | 0.000 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 772 | 772 (1.000) | 793 (0.816) | 1197 (0.204) | 2658 (0.200) | – | – | – | 0.000 | – | – | – | – | – | – | 0.000 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4248 | 4248 (1.000) | 9538 (0.215) | 5964 (0.420) | 9572 (0.214) | – | – | – | – | – | 0.000 | – | – | – | – | 0.000 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 2582 | 2582 (1.000) | 2807 (0.575) | 4588 (0.201) | infeasible (0.171) | – | – | – | – | – | 0.000 | – | – | – | – | 0.000 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 933 | 933 (1.000) | 1049 (0.571) | 1850 (0.202) | infeasible (0.160) | 0.000 | – | – | – | – | – | – | – | – | – | 0.000 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 1374 | 1374 (1.000) | 1406 (0.768) | 1550 (0.322) | infeasible (0.163) | 0.185 | – | – | – | – | – | – | – | – | – | 0.185 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 1676 | 1676 (1.000) | 1765 (0.468) | 2388 (0.200) | 3450 (0.200) | 0.170 | – | – | – | – | – | – | – | – | – | 0.170 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 1232 | 1232 (1.000) | 1618 (0.266) | 4601 (0.200) | 6441 (0.200) | 0.000 | – | – | – | – | – | – | – | – | – | 0.000 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 633 | 633 (1.000) | 795 (0.354) | 3925 (0.200) | infeasible (0.184) | – | 0.000 | – | – | – | – | – | – | – | – | 0.000 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 924 | 924 (1.000) | 1515 (0.200) | 1879 (0.200) | 3558 (0.200) | 0.000 | – | – | – | – | – | – | – | – | – | 0.000 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 1437 | 1437 (1.000) | 1909 (0.218) | 4831 (0.200) | infeasible (0.179) | – | – | – | – | – | – | 0.000 | – | – | – | 0.000 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 411 | 411 (1.000) | 417 (0.926) | 475 (0.483) | infeasible (0.179) | – | – | – | – | – | – | – | 0.797 | – | – | 0.797 | 18 | 18 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 1093 | 1093 (1.000) | 1286 (0.319) | 1999 (0.200) | 3107 (0.200) | – | – | – | – | – | – | – | – | 0.250 | – | 0.250 | 282 | 282 |

### fireworks_ai/glm-5p3-flash

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | lines-r6-glmflash r1 | lines-r6-glmflash-b r1 | lines-r6-glmflash-c r1 | lines-r6-glmflash-d r1 | lines-r6-glmflash-e r1 | lines-r6-glmflash-f r1 | lines-r6-glmflash-g r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 509 | 410 (1.000) | 410 (1.000) | 1554 (0.200) | 2318 (0.200) | 0.141 | – | – | – | – | – | – | 0.141 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 503 | 503 (1.000) | 613 (0.517) | 2459 (0.200) | infeasible (0.141) | – | – | – | – | – | 0.443 | – | 0.443 | 142 | 142 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 874 | 680 (1.000) | 680 (1.000) | 2941 (0.200) | infeasible (0.165) | – | – | 0.270 | – | – | – | – | 0.270 | -36 | 158 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 772 | 772 (1.000) | 793 (0.816) | 1197 (0.204) | 2658 (0.200) | – | – | – | 0.165 | – | – | – | 0.165 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4248 | 4248 (1.000) | 9538 (0.215) | 5964 (0.420) | 9572 (0.214) | – | – | – | 0.125 | – | – | – | 0.125 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 2582 | 2582 (1.000) | 2807 (0.575) | 4588 (0.201) | infeasible (0.171) | – | – | – | – | – | – | 0.171 | 0.171 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 933 | 933 (1.000) | 1049 (0.571) | 1850 (0.202) | infeasible (0.160) | 0.814 | – | – | – | – | – | – | 0.814 | 40 | 40 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 1374 | 1374 (1.000) | 1406 (0.768) | 1550 (0.322) | infeasible (0.163) | 0.373 | – | – | – | – | – | – | 0.373 | 143 | 143 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 1676 | 1676 (1.000) | 1765 (0.468) | 2388 (0.200) | 3450 (0.200) | 0.163 | – | – | – | – | – | – | 0.163 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 1232 | 1232 (1.000) | 1618 (0.266) | 4601 (0.200) | 6441 (0.200) | 0.160 | – | – | – | – | – | – | 0.160 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 633 | 633 (1.000) | 795 (0.354) | 3925 (0.200) | infeasible (0.184) | – | – | – | – | 0.152 | – | – | 0.152 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 924 | 924 (1.000) | 1515 (0.200) | 1879 (0.200) | 3558 (0.200) | 0.183 | – | – | – | – | – | – | 0.183 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 1437 | 1437 (1.000) | 1909 (0.218) | 4831 (0.200) | infeasible (0.179) | 0.000 | – | – | – | – | – | – | 0.000 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 411 | 411 (1.000) | 417 (0.926) | 475 (0.483) | infeasible (0.179) | 0.555 | – | – | – | – | – | – | 0.555 | 50 | 50 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 1093 | 1093 (1.000) | 1286 (0.319) | 1999 (0.200) | 3107 (0.200) | – | – | 0.200 | – | – | – | – | 0.200 | 858 | 858 |

### openai/gpt-6.1-sol

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 509 | 410 (1.000) | 410 (1.000) | 1554 (0.200) | 2318 (0.200) | 0.298 | 0.298 | 113 | 212 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 503 | 503 (1.000) | 613 (0.517) | 2459 (0.200) | infeasible (0.141) | 0.730 | 0.730 | 49 | 49 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 874 | 680 (1.000) | 680 (1.000) | 2941 (0.200) | infeasible (0.165) | 1.000 | 1.000 | -239 | -45 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 772 | 772 (1.000) | 793 (0.816) | 1197 (0.204) | 2658 (0.200) | 1.000 | 1.000 | -16 | -16 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4248 | 4248 (1.000) | 9538 (0.215) | 5964 (0.420) | 9572 (0.214) | 0.712 | 0.712 | 593 | 593 |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 2582 | 2582 (1.000) | 2807 (0.575) | 4588 (0.201) | infeasible (0.171) | 1.000 | 1.000 | -38 | -38 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 933 | 933 (1.000) | 1049 (0.571) | 1850 (0.202) | infeasible (0.160) | 0.410 | 0.410 | 202 | 202 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 1374 | 1374 (1.000) | 1406 (0.768) | 1550 (0.322) | infeasible (0.163) | 0.426 | 0.426 | 118 | 118 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 1676 | 1676 (1.000) | 1765 (0.468) | 2388 (0.200) | 3450 (0.200) | 0.437 | 0.437 | 99 | 99 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 1232 | 1232 (1.000) | 1618 (0.266) | 4601 (0.200) | 6441 (0.200) | 0.339 | 0.339 | 271 | 271 |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 633 | 633 (1.000) | 795 (0.354) | 3925 (0.200) | infeasible (0.184) | 0.288 | 0.288 | 217 | 217 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 924 | 924 (1.000) | 1515 (0.200) | 1879 (0.200) | 3558 (0.200) | 0.200 | 0.200 | 904 | 904 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 1437 | 1437 (1.000) | 1909 (0.218) | 4831 (0.200) | infeasible (0.179) | 0.186 | 0.186 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 411 | 411 (1.000) | 417 (0.926) | 475 (0.483) | infeasible (0.179) | 0.797 | 0.797 | 18 | 18 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 1093 | 1093 (1.000) | 1286 (0.319) | 1999 (0.200) | 3107 (0.200) | 0.210 | 0.210 | 440 | 440 |

### anthropic/claude-haiku-5-5

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 509 | 410 (1.000) | 410 (1.000) | 1554 (0.200) | 2318 (0.200) | 0.210 | 0.210 | 340 | 439 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 503 | 503 (1.000) | 613 (0.517) | 2459 (0.200) | infeasible (0.141) | 0.204 | 0.204 | 634 | 634 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 874 | 680 (1.000) | 680 (1.000) | 2941 (0.200) | infeasible (0.165) | 0.200 | 0.200 | 485 | 679 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 772 | 772 (1.000) | 793 (0.816) | 1197 (0.204) | 2658 (0.200) | 0.210 | 0.210 | 350 | 350 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4248 | 4248 (1.000) | 9538 (0.215) | 5964 (0.420) | 9572 (0.214) | 0.525 | 0.525 | 1196 | 1196 |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 2582 | 2582 (1.000) | 2807 (0.575) | 4588 (0.201) | infeasible (0.171) | 0.212 | 0.212 | 1251 | 1251 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 933 | 933 (1.000) | 1049 (0.571) | 1850 (0.202) | infeasible (0.160) | 0.399 | 0.399 | 210 | 210 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 1374 | 1374 (1.000) | 1406 (0.768) | 1550 (0.322) | infeasible (0.163) | 0.200 | 0.200 | 1002 | 1002 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 1676 | 1676 (1.000) | 1765 (0.468) | 2388 (0.200) | 3450 (0.200) | 0.200 | 0.200 | 773 | 773 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 1232 | 1232 (1.000) | 1618 (0.266) | 4601 (0.200) | 6441 (0.200) | 0.184 | 0.184 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 633 | 633 (1.000) | 795 (0.354) | 3925 (0.200) | infeasible (0.184) | 0.192 | 0.192 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 924 | 924 (1.000) | 1515 (0.200) | 1879 (0.200) | 3558 (0.200) | 0.200 | 0.200 | 1815 | 1815 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 1437 | 1437 (1.000) | 1909 (0.218) | 4831 (0.200) | infeasible (0.179) | 0.200 | 0.200 | 3785 | 3785 |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 411 | 411 (1.000) | 417 (0.926) | 475 (0.483) | infeasible (0.179) | 0.527 | 0.527 | 55 | 55 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 1093 | 1093 (1.000) | 1286 (0.319) | 1999 (0.200) | 3107 (0.200) | 0.200 | 0.200 | 1134 | 1134 |

### fireworks_ai/kimi-k3

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | lines-r6-kimi r1 | lines-r6-kimi-b r1 | lines-r6-kimi-c r1 | lines-r6-kimi-d r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 509 | 410 (1.000) | 410 (1.000) | 1554 (0.200) | 2318 (0.200) | 0.153 | – | – | – | 0.153 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 503 | 503 (1.000) | 613 (0.517) | 2459 (0.200) | infeasible (0.141) | – | 0.531 | – | – | 0.531 | 105 | 105 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 874 | 680 (1.000) | 680 (1.000) | 2941 (0.200) | infeasible (0.165) | – | – | 0.200 | – | 0.200 | 918 | 1112 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 772 | 772 (1.000) | 793 (0.816) | 1197 (0.204) | 2658 (0.200) | – | – | – | 0.289 | 0.289 | 177 | 177 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4248 | 4248 (1.000) | 9538 (0.215) | 5964 (0.420) | 9572 (0.214) | – | – | – | 0.581 | 0.581 | 986 | 986 |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 2582 | 2582 (1.000) | 2807 (0.575) | 4588 (0.201) | infeasible (0.171) | – | – | – | 0.171 | 0.171 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 933 | 933 (1.000) | 1049 (0.571) | 1850 (0.202) | infeasible (0.160) | 0.160 | – | – | – | 0.160 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 1374 | 1374 (1.000) | 1406 (0.768) | 1550 (0.322) | infeasible (0.163) | 0.185 | – | – | – | 0.185 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 1676 | 1676 (1.000) | 1765 (0.468) | 2388 (0.200) | 3450 (0.200) | 0.163 | – | – | – | 0.163 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 1232 | 1232 (1.000) | 1618 (0.266) | 4601 (0.200) | 6441 (0.200) | 0.192 | – | – | – | 0.192 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 633 | 633 (1.000) | 795 (0.354) | 3925 (0.200) | infeasible (0.184) | – | – | 0.112 | – | 0.112 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 924 | 924 (1.000) | 1515 (0.200) | 1879 (0.200) | 3558 (0.200) | 0.183 | – | – | – | 0.183 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 1437 | 1437 (1.000) | 1909 (0.218) | 4831 (0.200) | infeasible (0.179) | 0.193 | – | – | – | 0.193 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 411 | 411 (1.000) | 417 (0.926) | 475 (0.483) | infeasible (0.179) | 0.158 | – | – | – | 0.158 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 1093 | 1093 (1.000) | 1286 (0.319) | 1999 (0.200) | 3107 (0.200) | – | – | 0.200 | – | 0.200 | 757 | 757 |

### openai/gpt-6-luna

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 509 | 410 (1.000) | 410 (1.000) | 1554 (0.200) | 2318 (0.200) | 0.200 | 0.200 | 1766 | 1865 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 503 | 503 (1.000) | 613 (0.517) | 2459 (0.200) | infeasible (0.141) | 0.204 | 0.204 | 637 | 637 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 874 | 680 (1.000) | 680 (1.000) | 2941 (0.200) | infeasible (0.165) | 0.200 | 0.200 | 1295 | 1489 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 772 | 772 (1.000) | 793 (0.816) | 1197 (0.204) | 2658 (0.200) | 0.307 | 0.307 | 162 | 162 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4248 | 4248 (1.000) | 9538 (0.215) | 5964 (0.420) | 9572 (0.214) | 0.188 | 0.188 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 2582 | 2582 (1.000) | 2807 (0.575) | 4588 (0.201) | infeasible (0.171) | 0.201 | 0.201 | 1971 | 1971 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 933 | 933 (1.000) | 1049 (0.571) | 1850 (0.202) | infeasible (0.160) | 0.200 | 0.200 | 1214 | 1214 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 1374 | 1374 (1.000) | 1406 (0.768) | 1550 (0.322) | infeasible (0.163) | 0.276 | 0.276 | 220 | 220 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 1676 | 1676 (1.000) | 1765 (0.468) | 2388 (0.200) | 3450 (0.200) | 0.200 | 0.200 | 701 | 701 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 1232 | 1232 (1.000) | 1618 (0.266) | 4601 (0.200) | 6441 (0.200) | 0.200 | 0.200 | 6361 | 6361 |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 633 | 633 (1.000) | 795 (0.354) | 3925 (0.200) | infeasible (0.184) | 0.200 | 0.200 | 10468 | 10468 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 924 | 924 (1.000) | 1515 (0.200) | 1879 (0.200) | 3558 (0.200) | 0.192 | 0.192 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 1437 | 1437 (1.000) | 1909 (0.218) | 4831 (0.200) | infeasible (0.179) | 0.200 | 0.200 | 2002 | 2002 |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 411 | 411 (1.000) | 417 (0.926) | 475 (0.483) | infeasible (0.179) | 0.543 | 0.543 | 52 | 52 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 1093 | 1093 (1.000) | 1286 (0.319) | 1999 (0.200) | 3107 (0.200) | 0.200 | 0.200 | 1207 | 1207 |

### anthropic/claude-opus-5-5

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 509 | 410 (1.000) | 410 (1.000) | 1554 (0.200) | 2318 (0.200) | 0.279 | 0.279 | 135 | 234 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 503 | 503 (1.000) | 613 (0.517) | 2459 (0.200) | infeasible (0.141) | 0.827 | 0.827 | 29 | 29 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 874 | 680 (1.000) | 680 (1.000) | 2941 (0.200) | infeasible (0.165) | 0.816 | 0.816 | -177 | 17 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 772 | 772 (1.000) | 793 (0.816) | 1197 (0.204) | 2658 (0.200) | 1.000 | 1.000 | -10 | -10 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4248 | 4248 (1.000) | 9538 (0.215) | 5964 (0.420) | 9572 (0.214) | 0.759 | 0.759 | 476 | 476 |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 2582 | 2582 (1.000) | 2807 (0.575) | 4588 (0.201) | infeasible (0.171) | 0.657 | 0.657 | 166 | 166 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 933 | 933 (1.000) | 1049 (0.571) | 1850 (0.202) | infeasible (0.160) | 0.892 | 0.892 | 22 | 22 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 1374 | 1374 (1.000) | 1406 (0.768) | 1550 (0.322) | infeasible (0.163) | 0.927 | 0.927 | 9 | 9 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 1676 | 1676 (1.000) | 1765 (0.468) | 2388 (0.200) | 3450 (0.200) | 0.292 | 0.292 | 176 | 176 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 1232 | 1232 (1.000) | 1618 (0.266) | 4601 (0.200) | 6441 (0.200) | 0.564 | 0.564 | 122 | 122 |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 633 | 633 (1.000) | 795 (0.354) | 3925 (0.200) | infeasible (0.184) | 0.397 | 0.397 | 138 | 138 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 924 | 924 (1.000) | 1515 (0.200) | 1879 (0.200) | 3558 (0.200) | 0.175 | 0.175 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 1437 | 1437 (1.000) | 1909 (0.218) | 4831 (0.200) | infeasible (0.179) | 0.288 | 0.288 | 272 | 272 |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 411 | 411 (1.000) | 417 (0.926) | 475 (0.483) | infeasible (0.179) | 0.750 | 0.750 | 23 | 23 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 1093 | 1093 (1.000) | 1286 (0.319) | 1999 (0.200) | 3107 (0.200) | 0.277 | 0.277 | 237 | 237 |

### groq/qwen/qwen3.8-27b

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 509 | 410 (1.000) | 410 (1.000) | 1554 (0.200) | 2318 (0.200) | 0.059 | 0.059 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 503 | 503 (1.000) | 613 (0.517) | 2459 (0.200) | infeasible (0.141) | 0.176 | 0.176 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 874 | 680 (1.000) | 680 (1.000) | 2941 (0.200) | infeasible (0.165) | 0.200 | 0.200 | 1524 | 1718 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 772 | 772 (1.000) | 793 (0.816) | 1197 (0.204) | 2658 (0.200) | 0.118 | 0.118 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4248 | 4248 (1.000) | 9538 (0.215) | 5964 (0.420) | 9572 (0.214) | 0.163 | 0.163 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 2582 | 2582 (1.000) | 2807 (0.575) | 4588 (0.201) | infeasible (0.171) | 0.086 | 0.086 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 933 | 933 (1.000) | 1049 (0.571) | 1850 (0.202) | infeasible (0.160) | 0.133 | 0.133 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 1374 | 1374 (1.000) | 1406 (0.768) | 1550 (0.322) | infeasible (0.163) | 0.178 | 0.178 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 1676 | 1676 (1.000) | 1765 (0.468) | 2388 (0.200) | 3450 (0.200) | 0.133 | 0.133 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 1232 | 1232 (1.000) | 1618 (0.266) | 4601 (0.200) | 6441 (0.200) | 0.168 | 0.168 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 633 | 633 (1.000) | 795 (0.354) | 3925 (0.200) | infeasible (0.184) | 0.064 | 0.064 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 924 | 924 (1.000) | 1515 (0.200) | 1879 (0.200) | 3558 (0.200) | 0.183 | 0.183 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 1437 | 1437 (1.000) | 1909 (0.218) | 4831 (0.200) | infeasible (0.179) | 0.157 | 0.157 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 411 | 411 (1.000) | 417 (0.926) | 475 (0.483) | infeasible (0.179) | 0.137 | 0.137 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 1093 | 1093 (1.000) | 1286 (0.319) | 1999 (0.200) | 3107 (0.200) | 0.191 | 0.191 | – | – |

### fireworks_ai/qwen3p8-2p4t-a95b

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | lines-r6-qwen2t r1 | lines-r6-qwen2t-b r1 | lines-r6-qwen2t-c r1 | lines-r6-qwen2t-d r1 | lines-r6-qwen2t-e r1 | lines-r6-qwen2t-f r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 509 | 410 (1.000) | 410 (1.000) | 1554 (0.200) | 2318 (0.200) | 0.176 | – | – | – | – | – | 0.176 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 503 | 503 (1.000) | 613 (0.517) | 2459 (0.200) | infeasible (0.141) | – | 0.141 | – | – | – | – | 0.141 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 874 | 680 (1.000) | 680 (1.000) | 2941 (0.200) | infeasible (0.165) | – | – | – | – | 0.200 | – | 0.200 | 639 | 833 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 772 | 772 (1.000) | 793 (0.816) | 1197 (0.204) | 2658 (0.200) | – | – | – | 0.699 | – | – | 0.699 | 38 | 38 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4248 | 4248 (1.000) | 9538 (0.215) | 5964 (0.420) | 9572 (0.214) | – | – | – | 0.000 | – | – | 0.000 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 2582 | 2582 (1.000) | 2807 (0.575) | 4588 (0.201) | infeasible (0.171) | – | – | – | – | – | 0.143 | 0.143 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 933 | 933 (1.000) | 1049 (0.571) | 1850 (0.202) | infeasible (0.160) | 0.869 | – | – | – | – | – | 0.869 | 27 | 27 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 1374 | 1374 (1.000) | 1406 (0.768) | 1550 (0.322) | infeasible (0.163) | 0.387 | – | – | – | – | – | 0.387 | 136 | 136 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 1676 | 1676 (1.000) | 1765 (0.468) | 2388 (0.200) | 3450 (0.200) | 0.240 | – | – | – | – | – | 0.240 | 245 | 245 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 1232 | 1232 (1.000) | 1618 (0.266) | 4601 (0.200) | 6441 (0.200) | 0.000 | – | – | – | – | – | 0.000 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 633 | 633 (1.000) | 795 (0.354) | 3925 (0.200) | infeasible (0.184) | – | – | – | 0.201 | – | – | 0.201 | 637 | 637 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 924 | 924 (1.000) | 1515 (0.200) | 1879 (0.200) | 3558 (0.200) | 0.200 | – | – | – | – | – | 0.200 | 1106 | 1106 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 1437 | 1437 (1.000) | 1909 (0.218) | 4831 (0.200) | infeasible (0.179) | – | – | 0.179 | – | – | – | 0.179 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 411 | 411 (1.000) | 417 (0.926) | 475 (0.483) | infeasible (0.179) | – | – | 0.750 | – | – | – | 0.750 | 23 | 23 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 1093 | 1093 (1.000) | 1286 (0.319) | 1999 (0.200) | 3107 (0.200) | – | – | 0.174 | – | – | – | 0.174 | – | – |

### anthropic/claude-sonnet-5-5

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 509 | 410 (1.000) | 410 (1.000) | 1554 (0.200) | 2318 (0.200) | 0.223 | 0.223 | 258 | 357 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 503 | 503 (1.000) | 613 (0.517) | 2459 (0.200) | infeasible (0.141) | 0.762 | 0.762 | 42 | 42 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 874 | 680 (1.000) | 680 (1.000) | 2941 (0.200) | infeasible (0.165) | 0.753 | 0.753 | -170 | 24 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 772 | 772 (1.000) | 793 (0.816) | 1197 (0.204) | 2658 (0.200) | 0.566 | 0.566 | 63 | 63 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4248 | 4248 (1.000) | 9538 (0.215) | 5964 (0.420) | 9572 (0.214) | 0.897 | 0.897 | 183 | 183 |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 2582 | 2582 (1.000) | 2807 (0.575) | 4588 (0.201) | infeasible (0.171) | 0.203 | 0.203 | 1634 | 1634 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 933 | 933 (1.000) | 1049 (0.571) | 1850 (0.202) | infeasible (0.160) | 0.579 | 0.579 | 113 | 113 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 1374 | 1374 (1.000) | 1406 (0.768) | 1550 (0.322) | infeasible (0.163) | 0.330 | 0.330 | 170 | 170 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 1676 | 1676 (1.000) | 1765 (0.468) | 2388 (0.200) | 3450 (0.200) | 0.202 | 0.202 | 501 | 501 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 1232 | 1232 (1.000) | 1618 (0.266) | 4601 (0.200) | 6441 (0.200) | 0.200 | 0.200 | 1715 | 1715 |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 633 | 633 (1.000) | 795 (0.354) | 3925 (0.200) | infeasible (0.184) | 0.206 | 0.206 | 485 | 485 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 924 | 924 (1.000) | 1515 (0.200) | 1879 (0.200) | 3558 (0.200) | 0.200 | 0.200 | 851 | 851 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 1437 | 1437 (1.000) | 1909 (0.218) | 4831 (0.200) | infeasible (0.179) | 0.201 | 0.201 | 792 | 792 |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 411 | 411 (1.000) | 417 (0.926) | 475 (0.483) | infeasible (0.179) | 0.282 | 0.282 | 140 | 140 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 1093 | 1093 (1.000) | 1286 (0.319) | 1999 (0.200) | 3107 (0.200) | 0.200 | 0.200 | 799 | 799 |

## Unscored runs

| Sweep | Model | Task | Rep | Attempts | Last outcome | Spend |
|---|---|---|---:|---:|---|---:|
| lines-r6-dsflash | fireworks_ai/deepseek-v4p1-flash | dock-36A-w06x1-busy-0-e12 | 1 | 1 | AgentUnreachableError | $3.00 |
| lines-r6-dsflash | fireworks_ai/deepseek-v4p1-flash | dock-24B-w07x1-busy-0-e04 | 1 | 1 | no_instance | $3.00 |
| lines-r6-dsflash | fireworks_ai/deepseek-v4p1-flash | dock-24B-w07x1-busy-0-e09 | 1 | 0 | not run | $0.00 |
| lines-r6-dsflash | fireworks_ai/deepseek-v4p1-flash | dock-24B-w16x1-busy-0-e12 | 1 | 0 | not run | $0.00 |
| lines-r6-dsflash | fireworks_ai/deepseek-v4p1-flash | dock-24B-w35x1-busy-0-e00 | 1 | 0 | not run | $0.00 |
| lines-r6-dsflash-b | fireworks_ai/deepseek-v4p1-flash | dock-24B-w07x1-busy-0-e09 | 1 | 1 | AgentUnreachableError | $3.00 |
| lines-r6-dsflash-b | fireworks_ai/deepseek-v4p1-flash | dock-24B-w16x1-busy-0-e12 | 1 | 1 | no_instance | $3.00 |
| lines-r6-dsflash-b | fireworks_ai/deepseek-v4p1-flash | dock-24B-w35x1-busy-0-e00 | 1 | 1 | no_instance | $3.00 |
| lines-r6-glm | fireworks_ai/glm-5p3 | dock-36A-w17x1-busy-0-e12 | 1 | 1 | AgentUnreachableError | $10.00 |
| lines-r6-glm | fireworks_ai/glm-5p3 | dock-36A-w35x1-standard-0-e03 | 1 | 1 | no_instance | $10.00 |
| lines-r6-glm | fireworks_ai/glm-5p3 | dock-36A-w37x1-busy-0-e12 | 1 | 1 | no_instance | $10.00 |
| lines-r6-glm | fireworks_ai/glm-5p3 | dock-24B-w07x1-busy-0-e08 | 1 | 0 | not run | $0.00 |
| lines-r6-glm | fireworks_ai/glm-5p3 | dock-36A-w06x1-busy-0-e12 | 1 | 0 | not run | $0.00 |
| lines-r6-glm | fireworks_ai/glm-5p3 | dock-24B-w07x1-busy-0-e04 | 1 | 0 | not run | $0.00 |
| lines-r6-glm | fireworks_ai/glm-5p3 | dock-24B-w07x1-busy-0-e09 | 1 | 0 | not run | $0.00 |
| lines-r6-glm | fireworks_ai/glm-5p3 | dock-24B-w16x1-busy-0-e12 | 1 | 0 | not run | $0.00 |
| lines-r6-glm | fireworks_ai/glm-5p3 | dock-24B-w35x1-busy-0-e00 | 1 | 0 | not run | $0.00 |
| lines-r6-glm-b | fireworks_ai/glm-5p3 | dock-24B-w07x1-busy-0-e04 | 1 | 1 | AgentUnreachableError | $10.00 |
| lines-r6-glm-b | fireworks_ai/glm-5p3 | dock-24B-w07x1-busy-0-e09 | 1 | 1 | no_instance | $10.00 |
| lines-r6-glm-b | fireworks_ai/glm-5p3 | dock-24B-w16x1-busy-0-e12 | 1 | 1 | no_instance | $10.00 |
| lines-r6-glm-b | fireworks_ai/glm-5p3 | dock-24B-w35x1-busy-0-e00 | 1 | 0 | not run | $0.00 |
| lines-r6-glm-c | fireworks_ai/glm-5p3 | dock-36A-w17x1-busy-0-e12 | 1 | 1 | TimeoutError | $10.00 |
| lines-r6-glm-c | fireworks_ai/glm-5p3 | dock-36A-w35x1-standard-0-e03 | 1 | 0 | not run | $0.00 |
| lines-r6-glm-c | fireworks_ai/glm-5p3 | dock-36A-w37x1-busy-0-e12 | 1 | 0 | not run | $0.00 |
| lines-r6-glm-c | fireworks_ai/glm-5p3 | dock-24B-w07x1-busy-0-e08 | 1 | 0 | not run | $0.00 |
| lines-r6-glm-d | fireworks_ai/glm-5p3 | dock-24B-w16x1-busy-0-e12 | 1 | 1 | interrupted | $10.00 |
| lines-r6-glm-d | fireworks_ai/glm-5p3 | dock-24B-w35x1-busy-0-e00 | 1 | 0 | not run | $0.00 |
| lines-r6-glm-e | fireworks_ai/glm-5p3 | dock-36A-w37x1-busy-0-e12 | 1 | 0 | not run | $0.00 |
| lines-r6-glm-e | fireworks_ai/glm-5p3 | dock-24B-w07x1-busy-0-e08 | 1 | 0 | not run | $0.00 |
| lines-r6-glmflash | fireworks_ai/glm-5p3-flash | dock-36A-w37x1-busy-0-e12 | 1 | 1 | AgentUnreachableError | $1.00 |
| lines-r6-glmflash | fireworks_ai/glm-5p3-flash | dock-24B-w07x1-busy-0-e08 | 1 | 1 | no_instance | $1.00 |
| lines-r6-glmflash | fireworks_ai/glm-5p3-flash | dock-36A-w06x1-busy-0-e12 | 1 | 1 | no_instance | $1.00 |
| lines-r6-glmflash | fireworks_ai/glm-5p3-flash | dock-24B-w07x1-busy-0-e04 | 1 | 1 | no_instance | $1.00 |
| lines-r6-glmflash | fireworks_ai/glm-5p3-flash | dock-24B-w07x1-busy-0-e09 | 1 | 0 | not run | $0.00 |
| lines-r6-glmflash | fireworks_ai/glm-5p3-flash | dock-24B-w16x1-busy-0-e12 | 1 | 0 | not run | $0.00 |
| lines-r6-glmflash | fireworks_ai/glm-5p3-flash | dock-24B-w35x1-busy-0-e00 | 1 | 0 | not run | $0.00 |
| lines-r6-glmflash-b | fireworks_ai/glm-5p3-flash | dock-24B-w07x1-busy-0-e04 | 1 | 2 | no_instance | $2.00 |
| lines-r6-glmflash-b | fireworks_ai/glm-5p3-flash | dock-24B-w07x1-busy-0-e09 | 1 | 1 | no_instance | $1.00 |
| lines-r6-glmflash-b | fireworks_ai/glm-5p3-flash | dock-24B-w16x1-busy-0-e12 | 1 | 1 | no_instance | $1.00 |
| lines-r6-glmflash-b | fireworks_ai/glm-5p3-flash | dock-24B-w35x1-busy-0-e00 | 1 | 1 | no_instance | $1.00 |
| lines-r6-glmflash-c | fireworks_ai/glm-5p3-flash | dock-36A-w06x1-busy-0-e12 | 1 | 0 | not run | $0.00 |
| lines-r6-glmflash-c | fireworks_ai/glm-5p3-flash | dock-24B-w07x1-busy-0-e04 | 1 | 0 | not run | $0.00 |
| lines-r6-glmflash-d | fireworks_ai/glm-5p3-flash | dock-24B-w35x1-busy-0-e00 | 1 | 0 | not run | $0.00 |
| lines-r6-kimi | fireworks_ai/kimi-k3 | dock-36A-w37x1-busy-0-e12 | 1 | 1 | AgentUnreachableError | $10.00 |
| lines-r6-kimi | fireworks_ai/kimi-k3 | dock-24B-w07x1-busy-0-e08 | 1 | 0 | not run | $0.00 |
| lines-r6-kimi | fireworks_ai/kimi-k3 | dock-36A-w06x1-busy-0-e12 | 1 | 0 | not run | $0.00 |
| lines-r6-kimi | fireworks_ai/kimi-k3 | dock-24B-w07x1-busy-0-e04 | 1 | 0 | not run | $0.00 |
| lines-r6-kimi | fireworks_ai/kimi-k3 | dock-24B-w07x1-busy-0-e09 | 1 | 0 | not run | $0.00 |
| lines-r6-kimi | fireworks_ai/kimi-k3 | dock-24B-w16x1-busy-0-e12 | 1 | 0 | not run | $0.00 |
| lines-r6-kimi | fireworks_ai/kimi-k3 | dock-24B-w35x1-busy-0-e00 | 1 | 0 | not run | $0.00 |
| lines-r6-kimi-b | fireworks_ai/kimi-k3 | dock-24B-w07x1-busy-0-e09 | 1 | 1 | AgentUnreachableError | $10.00 |
| lines-r6-kimi-b | fireworks_ai/kimi-k3 | dock-24B-w16x1-busy-0-e12 | 1 | 1 | no_instance | $10.00 |
| lines-r6-kimi-b | fireworks_ai/kimi-k3 | dock-24B-w35x1-busy-0-e00 | 1 | 1 | no_instance | $10.00 |
| lines-r6-qwen2t | fireworks_ai/qwen3p8-2p4t-a95b | dock-36A-w17x1-busy-0-e12 | 1 | 1 | AgentUnreachableError | $10.00 |
| lines-r6-qwen2t | fireworks_ai/qwen3p8-2p4t-a95b | dock-36A-w35x1-standard-0-e03 | 1 | 1 | no_instance | $10.00 |
| lines-r6-qwen2t | fireworks_ai/qwen3p8-2p4t-a95b | dock-36A-w37x1-busy-0-e12 | 1 | 0 | not run | $0.00 |
| lines-r6-qwen2t | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w07x1-busy-0-e08 | 1 | 0 | not run | $0.00 |
| lines-r6-qwen2t | fireworks_ai/qwen3p8-2p4t-a95b | dock-36A-w06x1-busy-0-e12 | 1 | 0 | not run | $0.00 |
| lines-r6-qwen2t | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w07x1-busy-0-e04 | 1 | 0 | not run | $0.00 |
| lines-r6-qwen2t | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w07x1-busy-0-e09 | 1 | 0 | not run | $0.00 |
| lines-r6-qwen2t | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w16x1-busy-0-e12 | 1 | 0 | not run | $0.00 |
| lines-r6-qwen2t | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w35x1-busy-0-e00 | 1 | 0 | not run | $0.00 |
| lines-r6-qwen2t-b | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w07x1-busy-0-e09 | 1 | 1 | AgentUnreachableError | $10.00 |
| lines-r6-qwen2t-b | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w16x1-busy-0-e12 | 1 | 1 | no_instance | $10.00 |
| lines-r6-qwen2t-b | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w35x1-busy-0-e00 | 1 | 1 | no_instance | $10.00 |
| lines-r6-qwen2t-c | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w07x1-busy-0-e08 | 1 | 0 | not run | $0.00 |
| lines-r6-qwen2t-d | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w35x1-busy-0-e00 | 1 | 0 | not run | $0.00 |

## Runs whose agent reward differs from the verifier's

Only runs whose agent saw the week end.

None.
