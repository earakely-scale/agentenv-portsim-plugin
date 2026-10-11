# PortSim lines: portsim-llm on the wind weeks with the ships' agents

Sweeps: `lines-astra` (openai/gpt-6-astra; 15 tasks, k=1, episode cap $15); `lines-dsflash` (fireworks_ai/deepseek-v4p1-flash; 15 tasks, k=1, episode cap $3); `lines-dsflash-2` (fireworks_ai/deepseek-v4p1-flash; 1 tasks, k=1, episode cap $3); `lines-glm` (fireworks_ai/glm-5p3; 15 tasks, k=1, episode cap $10); `lines-glm-2` (fireworks_ai/glm-5p3; 2 tasks, k=1, episode cap $10); `lines-glm-3` (fireworks_ai/glm-5p3; 2 tasks, k=1, episode cap $10); `lines-glmflash` (fireworks_ai/glm-5p3-flash; 15 tasks, k=1, episode cap $1); `lines-glmflash-2` (fireworks_ai/glm-5p3-flash; 3 tasks, k=1, episode cap $1); `lines-glmflash-3` (fireworks_ai/glm-5p3-flash; 1 tasks, k=1, episode cap $1); `lines-gpt` (openai/gpt-6.1-sol; 15 tasks, k=1, episode cap $3); `lines-gpt-2` (openai/gpt-6.1-sol; 1 tasks, k=1, episode cap $3); `lines-haiku` (anthropic/claude-haiku-5-5; 15 tasks, k=1, episode cap $1); `lines-kimi` (fireworks_ai/kimi-k3; 15 tasks, k=1, episode cap $10); `lines-kimi-2` (fireworks_ai/kimi-k3; 1 tasks, k=1, episode cap $10); `lines-kimi-3` (fireworks_ai/kimi-k3; 1 tasks, k=1, episode cap $10); `lines-luna` (openai/gpt-6-luna; 15 tasks, k=1, episode cap $1); `lines-opus` (anthropic/claude-opus-5-5; 15 tasks, k=1, episode cap $15); `lines-opus-2` (anthropic/claude-opus-5-5; 1 tasks, k=1, episode cap $15); `lines-qwen27b` (groq/qwen/qwen3.8-27b; 15 tasks, k=1, episode cap $10); `lines-qwen2t` (fireworks_ai/qwen3p8-2p4t-a95b; 15 tasks, k=1, episode cap $10); `lines-qwen2t-2` (fireworks_ai/qwen3p8-2p4t-a95b; 3 tasks, k=1, episode cap $10); `lines-sonnet` (anthropic/claude-sonnet-5-5; 15 tasks, k=1, episode cap $10).
Harness: portsim-llm, with each ship's agent a portsim-line agent it can message. References, on the same weeks (data/lines/references.jsonl): hindsight, the clairvoyant CP-SAT optimum that knows every arrival and slows ships from the first watch it could ask; the anchor that rewards and regret are scored against, the lower of that cost and the follower's best over its four solver configurations; the follower, in its first configuration, which re-plans at every watch on the arrivals as known and requests arrival times through the ships' agents; silent, the same never asking them; and the naive online policy.

Spend: $195.41 known; 31 attempts with no spend recorded, $224.00 at the cap. Attempts: 282, retries: 86. Unscored runs: 16 of 196.

## Per model

| Model | Tasks | Runs scored/planned | Mean reward (95% CI) | Follower reference | Silent reference | Naive reference | Reached done per rep | Feasible | At the anchor | Mean regret vs anchor | Mean regret vs hindsight | Mean excused cost | Mean hours at anchor | Messages per episode | Median turns | Tokens in/out per episode | Cached tokens per episode | Cost per episode | Spend |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| openai/gpt-6-astra | 15 | 15/15 | 0.691 (0.553 to 0.810) | 0.485 | 0.116 | 0.137 | 15 | 13 | 3 | 54.077 | 54.077 | 1.333 | 31.133 | 45.867 | 43 | 1087.0k/5.3k | 1040.1k | $1.7718 | $26.58 |
| fireworks_ai/deepseek-v4p1-flash | 15 | 15/16 | 0.072 (0.037 to 0.108) | 0.485 | 0.116 | 0.137 | 6 | 0 | 0 | – | – | 7.867 | 17.600 | 8.333 | 15 | 705.9k/226.0k | 636.7k | $0.2958 | $4.44 + 4 unknown |
| fireworks_ai/glm-5p3 | 15 | 15/19 | 0.085 (0.017 to 0.199) | 0.485 | 0.116 | 0.137 | 4 | 1 | 0 | 44.000 | 44.000 | 3.933 | 4.267 | 9.600 | 2 | 338.7k/136.9k | 306.3k | $0.7768 | $11.65 + 6 unknown |
| fireworks_ai/glm-5p3-flash | 15 | 15/19 | 0.096 (0.070 to 0.119) | 0.485 | 0.116 | 0.137 | 13 | 0 | 0 | – | – | 16.267 | 20.733 | 23.733 | 25 | 770.5k/179.9k | 688.6k | $0.1361 | $2.04 + 5 unknown |
| openai/gpt-6.1-sol | 15 | 15/16 | 0.394 (0.279 to 0.533) | 0.485 | 0.116 | 0.137 | 15 | 8 | 1 | 125.500 | 125.500 | 5.267 | 40.200 | 53.267 | 40 | 1088.8k/7.2k | 1032.3k | $0.2880 | $4.32 |
| anthropic/claude-haiku-5-5 | 15 | 15/15 | 0.142 (0.129 to 0.152) | 0.485 | 0.116 | 0.137 | 15 | 0 | 0 | – | – | 17.467 | 70.600 | 16.867 | 22 | 2509.0k/98.4k | 2343.4k | $0.0933 | $1.40 + 1 unknown |
| fireworks_ai/kimi-k3 | 15 | 15/17 | 0.133 (0.083 to 0.215) | 0.485 | 0.116 | 0.137 | 14 | 2 | 0 | 129.000 | 129.000 | 30.600 | 50.800 | 24.800 | 25 | 754.7k/84.9k | 696.5k | $1.6564 | $31.98 + 6 unknown |
| openai/gpt-6-luna | 15 | 15/15 | 0.144 (0.132 to 0.156) | 0.485 | 0.116 | 0.137 | 14 | 0 | 0 | – | – | 12.200 | 323.133 | 3.600 | 34 | 1949.1k/58.1k | 1844.6k | $0.0580 | $0.87 + 1 unknown |
| anthropic/claude-opus-5-5 | 15 | 15/16 | 0.315 (0.180 to 0.471) | 0.485 | 0.116 | 0.137 | 15 | 5 | 1 | 49.600 | 49.600 | 5.400 | 35.133 | 35.067 | 40 | 2110.7k/36.0k | 2008.6k | $2.0334 | $30.50 + 1 unknown |
| groq/qwen/qwen3.8-27b | 15 | 15/15 | 0.037 (0.020 to 0.057) | 0.485 | 0.116 | 0.137 | 13 | 0 | 0 | – | – | 25.800 | 151.000 | 0.200 | 29 | 1117.0k/18.2k | 0.0k | $0.9665 | $16.78 |
| fireworks_ai/qwen3p8-2p4t-a95b | 15 | 15/18 | 0.106 (0.072 to 0.135) | 0.485 | 0.116 | 0.137 | 10 | 0 | 0 | – | – | 12.400 | 41.800 | 27.400 | 36 | 1237.1k/347.4k | 1175.2k | $2.7262 | $40.89 + 6 unknown |
| anthropic/claude-sonnet-5-5 | 15 | 15/15 | 0.228 (0.159 to 0.328) | 0.485 | 0.116 | 0.137 | 15 | 3 | 0 | 434.000 | 434.000 | 14.333 | 40.133 | 39.600 | 30 | 2473.1k/71.6k | 2330.0k | $1.5976 | $23.96 + 1 unknown |

## Week by week

Hindsight as its cost; the anchor and the references as cost (reward).

### openai/gpt-6-astra

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 | 139 (1.000) | 326 (0.313) | infeasible (0.165) | infeasible (0.129) | 0.588 | 0.588 | 69 | 69 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 282 | 282 (1.000) | 342 (0.646) | infeasible (0.141) | infeasible (0.141) | 0.581 | 0.581 | 76 | 76 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 282 | 282 (1.000) | 335 (0.677) | infeasible (0.059) | infeasible (0.165) | 0.769 | 0.769 | 35 | 35 |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 292 | 292 (1.000) | 587 (0.251) | infeasible (0.141) | infeasible (0.153) | 0.684 | 0.684 | 54 | 54 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4406 | 4406 (1.000) | 4683 (0.891) | infeasible (0.125) | infeasible (0.100) | 0.878 | 0.878 | 313 | 313 |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1759 | 1759 (1.000) | 2631 (0.318) | infeasible (0.114) | infeasible (0.100) | 0.171 | 0.171 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 376 | 376 (1.000) | 407 (0.839) | infeasible (0.133) | infeasible (0.147) | 1.000 | 1.000 | -35 | -35 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 413 | 413 (1.000) | 539 (0.339) | infeasible (0.119) | infeasible (0.163) | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 413 | 413 (1.000) | 661 (0.226) | infeasible (0.119) | infeasible (0.141) | 1.000 | 1.000 | 0 | 0 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 | 40 (1.000) | 372 (0.207) | infeasible (0.056) | infeasible (0.128) | 0.184 | 0.184 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 | 40 (1.000) | 292 (0.222) | infeasible (0.080) | infeasible (0.152) | 0.397 | 0.397 | 98 | 98 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 15 | 15 (1.000) | 64 (0.541) | infeasible (0.142) | infeasible (0.158) | 0.849 | 0.849 | 12 | 12 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 211 | 211 (1.000) | 493 (0.228) | infeasible (0.093) | infeasible (0.093) | 0.648 | 0.648 | 49 | 49 |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 31 | 31 (1.000) | 61 (0.706) | infeasible (0.147) | infeasible (0.158) | 0.836 | 0.836 | 15 | 15 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 | 113 (1.000) | 122 (0.874) | infeasible (0.104) | infeasible (0.122) | 0.779 | 0.779 | 17 | 17 |

### fireworks_ai/deepseek-v4p1-flash

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | lines-dsflash r1 | lines-dsflash-2 r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 | 139 (1.000) | 326 (0.313) | infeasible (0.165) | infeasible (0.129) | 0.165 | – | 0.165 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 282 | 282 (1.000) | 342 (0.646) | infeasible (0.141) | infeasible (0.141) | 0.141 | – | 0.141 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 282 | 282 (1.000) | 335 (0.677) | infeasible (0.059) | infeasible (0.165) | 0.129 | – | 0.129 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 292 | 292 (1.000) | 587 (0.251) | infeasible (0.141) | infeasible (0.153) | 0.118 | – | 0.118 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4406 | 4406 (1.000) | 4683 (0.891) | infeasible (0.125) | infeasible (0.100) | 0.100 | – | 0.100 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1759 | 1759 (1.000) | 2631 (0.318) | infeasible (0.114) | infeasible (0.100) | 0.000 | – | 0.000 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 376 | 376 (1.000) | 407 (0.839) | infeasible (0.133) | infeasible (0.147) | 0.000 | – | 0.000 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 413 | 413 (1.000) | 539 (0.339) | infeasible (0.119) | infeasible (0.163) | 0.141 | – | 0.141 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 413 | 413 (1.000) | 661 (0.226) | infeasible (0.119) | infeasible (0.141) | 0.148 | – | 0.148 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 | 40 (1.000) | 372 (0.207) | infeasible (0.056) | infeasible (0.128) | 0.000 | – | 0.000 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 | 40 (1.000) | 292 (0.222) | infeasible (0.080) | infeasible (0.152) | 0.000 | – | 0.000 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 15 | 15 (1.000) | 64 (0.541) | infeasible (0.142) | infeasible (0.158) | 0.000 | – | 0.000 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 211 | 211 (1.000) | 493 (0.228) | infeasible (0.093) | infeasible (0.093) | – | 0.000 | 0.000 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 31 | 31 (1.000) | 61 (0.706) | infeasible (0.147) | infeasible (0.158) | 0.137 | – | 0.137 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 | 113 (1.000) | 122 (0.874) | infeasible (0.104) | infeasible (0.122) | 0.000 | – | 0.000 | – | – |

### fireworks_ai/glm-5p3

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | lines-glm r1 | lines-glm-2 r1 | lines-glm-3 r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 | 139 (1.000) | 326 (0.313) | infeasible (0.165) | infeasible (0.129) | 0.705 | – | – | 0.705 | 44 | 44 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 282 | 282 (1.000) | 342 (0.646) | infeasible (0.141) | infeasible (0.141) | – | – | 0.165 | 0.165 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 282 | 282 (1.000) | 335 (0.677) | infeasible (0.059) | infeasible (0.165) | 0.000 | – | – | 0.000 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 292 | 292 (1.000) | 587 (0.251) | infeasible (0.141) | infeasible (0.153) | 0.153 | – | – | 0.153 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4406 | 4406 (1.000) | 4683 (0.891) | infeasible (0.125) | infeasible (0.100) | – | – | 0.000 | 0.000 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1759 | 1759 (1.000) | 2631 (0.318) | infeasible (0.114) | infeasible (0.100) | 0.000 | – | – | 0.000 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 376 | 376 (1.000) | 407 (0.839) | infeasible (0.133) | infeasible (0.147) | 0.000 | – | – | 0.000 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 413 | 413 (1.000) | 539 (0.339) | infeasible (0.119) | infeasible (0.163) | 0.000 | – | – | 0.000 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 413 | 413 (1.000) | 661 (0.226) | infeasible (0.119) | infeasible (0.141) | 0.163 | – | – | 0.163 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 | 40 (1.000) | 372 (0.207) | infeasible (0.056) | infeasible (0.128) | 0.000 | – | – | 0.000 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 | 40 (1.000) | 292 (0.222) | infeasible (0.080) | infeasible (0.152) | 0.096 | – | – | 0.096 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 15 | 15 (1.000) | 64 (0.541) | infeasible (0.142) | infeasible (0.158) | 0.000 | – | – | 0.000 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 211 | 211 (1.000) | 493 (0.228) | infeasible (0.093) | infeasible (0.093) | 0.000 | – | – | 0.000 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 31 | 31 (1.000) | 61 (0.706) | infeasible (0.147) | infeasible (0.158) | 0.000 | – | – | 0.000 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 | 113 (1.000) | 122 (0.874) | infeasible (0.104) | infeasible (0.122) | 0.000 | – | – | 0.000 | – | – |

### fireworks_ai/glm-5p3-flash

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | lines-glmflash r1 | lines-glmflash-2 r1 | lines-glmflash-3 r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 | 139 (1.000) | 326 (0.313) | infeasible (0.165) | infeasible (0.129) | 0.141 | – | – | 0.141 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 282 | 282 (1.000) | 342 (0.646) | infeasible (0.141) | infeasible (0.141) | 0.082 | – | – | 0.082 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 282 | 282 (1.000) | 335 (0.677) | infeasible (0.059) | infeasible (0.165) | 0.129 | – | – | 0.129 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 292 | 292 (1.000) | 587 (0.251) | infeasible (0.141) | infeasible (0.153) | 0.106 | – | – | 0.106 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4406 | 4406 (1.000) | 4683 (0.891) | infeasible (0.125) | infeasible (0.100) | – | 0.025 | – | 0.025 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1759 | 1759 (1.000) | 2631 (0.318) | infeasible (0.114) | infeasible (0.100) | – | – | 0.000 | 0.000 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 376 | 376 (1.000) | 407 (0.839) | infeasible (0.133) | infeasible (0.147) | 0.160 | – | – | 0.160 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 413 | 413 (1.000) | 539 (0.339) | infeasible (0.119) | infeasible (0.163) | 0.133 | – | – | 0.133 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 413 | 413 (1.000) | 661 (0.226) | infeasible (0.119) | infeasible (0.141) | 0.111 | – | – | 0.111 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 | 40 (1.000) | 372 (0.207) | infeasible (0.056) | infeasible (0.128) | 0.000 | – | – | 0.000 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 | 40 (1.000) | 292 (0.222) | infeasible (0.080) | infeasible (0.152) | 0.120 | – | – | 0.120 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 15 | 15 (1.000) | 64 (0.541) | infeasible (0.142) | infeasible (0.158) | 0.092 | – | – | 0.092 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 211 | 211 (1.000) | 493 (0.228) | infeasible (0.093) | infeasible (0.093) | – | 0.071 | – | 0.071 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 31 | 31 (1.000) | 61 (0.706) | infeasible (0.147) | infeasible (0.158) | 0.116 | – | – | 0.116 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 | 113 (1.000) | 122 (0.874) | infeasible (0.104) | infeasible (0.122) | 0.157 | – | – | 0.157 | – | – |

### openai/gpt-6.1-sol

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | lines-gpt r1 | lines-gpt-2 r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 | 139 (1.000) | 326 (0.313) | infeasible (0.165) | infeasible (0.129) | 0.694 | – | 0.694 | 46 | 46 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 282 | 282 (1.000) | 342 (0.646) | infeasible (0.141) | infeasible (0.141) | 0.585 | – | 0.585 | 75 | 75 |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 282 | 282 (1.000) | 335 (0.677) | infeasible (0.059) | infeasible (0.165) | 0.153 | – | 0.153 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 292 | 292 (1.000) | 587 (0.251) | infeasible (0.141) | infeasible (0.153) | 0.346 | – | 0.346 | 183 | 183 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4406 | 4406 (1.000) | 4683 (0.891) | infeasible (0.125) | infeasible (0.100) | 0.188 | – | 0.188 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1759 | 1759 (1.000) | 2631 (0.318) | infeasible (0.114) | infeasible (0.100) | 0.441 | – | 0.441 | 548 | 548 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 376 | 376 (1.000) | 407 (0.839) | infeasible (0.133) | infeasible (0.147) | 1.000 | – | 1.000 | -40 | -40 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 413 | 413 (1.000) | 539 (0.339) | infeasible (0.119) | infeasible (0.163) | – | 0.429 | 0.429 | 90 | 90 |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 413 | 413 (1.000) | 661 (0.226) | infeasible (0.119) | infeasible (0.141) | 0.699 | – | 0.699 | 34 | 34 |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 | 40 (1.000) | 372 (0.207) | infeasible (0.056) | infeasible (0.128) | 0.152 | – | 0.152 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 | 40 (1.000) | 292 (0.222) | infeasible (0.080) | infeasible (0.152) | 0.503 | – | 0.503 | 68 | 68 |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 15 | 15 (1.000) | 64 (0.541) | infeasible (0.142) | infeasible (0.158) | 0.183 | – | 0.183 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 211 | 211 (1.000) | 493 (0.228) | infeasible (0.093) | infeasible (0.093) | 0.186 | – | 0.186 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 31 | 31 (1.000) | 61 (0.706) | infeasible (0.147) | infeasible (0.158) | 0.179 | – | 0.179 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 | 113 (1.000) | 122 (0.874) | infeasible (0.104) | infeasible (0.122) | 0.174 | – | 0.174 | – | – |

### anthropic/claude-haiku-5-5

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 | 139 (1.000) | 326 (0.313) | infeasible (0.165) | infeasible (0.129) | 0.176 | 0.176 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 282 | 282 (1.000) | 342 (0.646) | infeasible (0.141) | infeasible (0.141) | 0.129 | 0.129 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 282 | 282 (1.000) | 335 (0.677) | infeasible (0.059) | infeasible (0.165) | 0.141 | 0.141 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 292 | 292 (1.000) | 587 (0.251) | infeasible (0.141) | infeasible (0.153) | 0.141 | 0.141 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4406 | 4406 (1.000) | 4683 (0.891) | infeasible (0.125) | infeasible (0.100) | 0.150 | 0.150 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1759 | 1759 (1.000) | 2631 (0.318) | infeasible (0.114) | infeasible (0.100) | 0.086 | 0.086 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 376 | 376 (1.000) | 407 (0.839) | infeasible (0.133) | infeasible (0.147) | 0.160 | 0.160 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 413 | 413 (1.000) | 539 (0.339) | infeasible (0.119) | infeasible (0.163) | 0.141 | 0.141 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 413 | 413 (1.000) | 661 (0.226) | infeasible (0.119) | infeasible (0.141) | 0.141 | 0.141 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 | 40 (1.000) | 372 (0.207) | infeasible (0.056) | infeasible (0.128) | 0.128 | 0.128 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 | 40 (1.000) | 292 (0.222) | infeasible (0.080) | infeasible (0.152) | 0.152 | 0.152 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 15 | 15 (1.000) | 64 (0.541) | infeasible (0.142) | infeasible (0.158) | 0.175 | 0.175 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 211 | 211 (1.000) | 493 (0.228) | infeasible (0.093) | infeasible (0.093) | 0.107 | 0.107 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 31 | 31 (1.000) | 61 (0.706) | infeasible (0.147) | infeasible (0.158) | 0.147 | 0.147 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 | 113 (1.000) | 122 (0.874) | infeasible (0.104) | infeasible (0.122) | 0.148 | 0.148 | – | – |

### fireworks_ai/kimi-k3

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | lines-kimi r1 | lines-kimi-2 r1 | lines-kimi-3 r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 | 139 (1.000) | 326 (0.313) | infeasible (0.165) | infeasible (0.129) | 0.082 | – | – | 0.082 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 282 | 282 (1.000) | 342 (0.646) | infeasible (0.141) | infeasible (0.141) | 0.059 | – | – | 0.059 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 282 | 282 (1.000) | 335 (0.677) | infeasible (0.059) | infeasible (0.165) | 0.082 | – | – | 0.082 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 292 | 292 (1.000) | 587 (0.251) | infeasible (0.141) | infeasible (0.153) | 0.106 | – | – | 0.106 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4406 | 4406 (1.000) | 4683 (0.891) | infeasible (0.125) | infeasible (0.100) | 0.062 | – | – | 0.062 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1759 | 1759 (1.000) | 2631 (0.318) | infeasible (0.114) | infeasible (0.100) | 0.114 | – | – | 0.114 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 376 | 376 (1.000) | 407 (0.839) | infeasible (0.133) | infeasible (0.147) | 0.133 | – | – | 0.133 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 413 | 413 (1.000) | 539 (0.339) | infeasible (0.119) | infeasible (0.163) | 0.081 | – | – | 0.081 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 413 | 413 (1.000) | 661 (0.226) | infeasible (0.119) | infeasible (0.141) | 0.119 | – | – | 0.119 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 | 40 (1.000) | 372 (0.207) | infeasible (0.056) | infeasible (0.128) | 0.120 | – | – | 0.120 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 | 40 (1.000) | 292 (0.222) | infeasible (0.080) | infeasible (0.152) | – | – | 0.064 | 0.064 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 15 | 15 (1.000) | 64 (0.541) | infeasible (0.142) | infeasible (0.158) | 0.042 | – | – | 0.042 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 211 | 211 (1.000) | 493 (0.228) | infeasible (0.093) | infeasible (0.093) | 0.071 | – | – | 0.071 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 31 | 31 (1.000) | 61 (0.706) | infeasible (0.147) | infeasible (0.158) | 0.641 | – | – | 0.641 | 39 | 39 |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 | 113 (1.000) | 122 (0.874) | infeasible (0.104) | infeasible (0.122) | 0.212 | – | – | 0.212 | 219 | 219 |

### openai/gpt-6-luna

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 | 139 (1.000) | 326 (0.313) | infeasible (0.165) | infeasible (0.129) | 0.188 | 0.188 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 282 | 282 (1.000) | 342 (0.646) | infeasible (0.141) | infeasible (0.141) | 0.141 | 0.141 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 282 | 282 (1.000) | 335 (0.677) | infeasible (0.059) | infeasible (0.165) | 0.118 | 0.118 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 292 | 292 (1.000) | 587 (0.251) | infeasible (0.141) | infeasible (0.153) | 0.129 | 0.129 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4406 | 4406 (1.000) | 4683 (0.891) | infeasible (0.125) | infeasible (0.100) | 0.100 | 0.100 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1759 | 1759 (1.000) | 2631 (0.318) | infeasible (0.114) | infeasible (0.100) | 0.129 | 0.129 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 376 | 376 (1.000) | 407 (0.839) | infeasible (0.133) | infeasible (0.147) | 0.173 | 0.173 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 413 | 413 (1.000) | 539 (0.339) | infeasible (0.119) | infeasible (0.163) | 0.126 | 0.126 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 413 | 413 (1.000) | 661 (0.226) | infeasible (0.119) | infeasible (0.141) | 0.133 | 0.133 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 | 40 (1.000) | 372 (0.207) | infeasible (0.056) | infeasible (0.128) | 0.128 | 0.128 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 | 40 (1.000) | 292 (0.222) | infeasible (0.080) | infeasible (0.152) | 0.160 | 0.160 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 15 | 15 (1.000) | 64 (0.541) | infeasible (0.142) | infeasible (0.158) | 0.167 | 0.167 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 211 | 211 (1.000) | 493 (0.228) | infeasible (0.093) | infeasible (0.093) | 0.136 | 0.136 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 31 | 31 (1.000) | 61 (0.706) | infeasible (0.147) | infeasible (0.158) | 0.158 | 0.158 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 | 113 (1.000) | 122 (0.874) | infeasible (0.104) | infeasible (0.122) | 0.174 | 0.174 | – | – |

### anthropic/claude-opus-5-5

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | lines-opus r1 | lines-opus-2 r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 | 139 (1.000) | 326 (0.313) | infeasible (0.165) | infeasible (0.129) | 0.822 | – | 0.822 | 24 | 24 |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 282 | 282 (1.000) | 342 (0.646) | infeasible (0.141) | infeasible (0.141) | 0.141 | – | 0.141 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 282 | 282 (1.000) | 335 (0.677) | infeasible (0.059) | infeasible (0.165) | 0.129 | – | 0.129 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 292 | 292 (1.000) | 587 (0.251) | infeasible (0.141) | infeasible (0.153) | 0.645 | – | 0.645 | 63 | 63 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4406 | 4406 (1.000) | 4683 (0.891) | infeasible (0.125) | infeasible (0.100) | – | 0.125 | 0.125 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1759 | 1759 (1.000) | 2631 (0.318) | infeasible (0.114) | infeasible (0.100) | 0.086 | – | 0.086 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 376 | 376 (1.000) | 407 (0.839) | infeasible (0.133) | infeasible (0.147) | 1.000 | – | 1.000 | -60 | -60 |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 413 | 413 (1.000) | 539 (0.339) | infeasible (0.119) | infeasible (0.163) | 0.156 | – | 0.156 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 413 | 413 (1.000) | 661 (0.226) | infeasible (0.119) | infeasible (0.141) | 0.170 | – | 0.170 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 | 40 (1.000) | 372 (0.207) | infeasible (0.056) | infeasible (0.128) | 0.128 | – | 0.128 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 | 40 (1.000) | 292 (0.222) | infeasible (0.080) | infeasible (0.152) | 0.160 | – | 0.160 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 15 | 15 (1.000) | 64 (0.541) | infeasible (0.142) | infeasible (0.158) | 0.228 | – | 0.228 | 193 | 193 |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 211 | 211 (1.000) | 493 (0.228) | infeasible (0.093) | infeasible (0.093) | 0.114 | – | 0.114 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 31 | 31 (1.000) | 61 (0.706) | infeasible (0.147) | infeasible (0.158) | 0.147 | – | 0.147 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 | 113 (1.000) | 122 (0.874) | infeasible (0.104) | infeasible (0.122) | 0.669 | – | 0.669 | 28 | 28 |

### groq/qwen/qwen3.8-27b

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 | 139 (1.000) | 326 (0.313) | infeasible (0.165) | infeasible (0.129) | 0.059 | 0.059 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 282 | 282 (1.000) | 342 (0.646) | infeasible (0.141) | infeasible (0.141) | 0.000 | 0.000 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 282 | 282 (1.000) | 335 (0.677) | infeasible (0.059) | infeasible (0.165) | 0.000 | 0.000 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 292 | 292 (1.000) | 587 (0.251) | infeasible (0.141) | infeasible (0.153) | 0.024 | 0.024 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4406 | 4406 (1.000) | 4683 (0.891) | infeasible (0.125) | infeasible (0.100) | 0.100 | 0.100 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1759 | 1759 (1.000) | 2631 (0.318) | infeasible (0.114) | infeasible (0.100) | 0.014 | 0.014 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 376 | 376 (1.000) | 407 (0.839) | infeasible (0.133) | infeasible (0.147) | 0.027 | 0.027 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 413 | 413 (1.000) | 539 (0.339) | infeasible (0.119) | infeasible (0.163) | 0.067 | 0.067 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 413 | 413 (1.000) | 661 (0.226) | infeasible (0.119) | infeasible (0.141) | 0.015 | 0.015 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 | 40 (1.000) | 372 (0.207) | infeasible (0.056) | infeasible (0.128) | 0.000 | 0.000 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 | 40 (1.000) | 292 (0.222) | infeasible (0.080) | infeasible (0.152) | 0.016 | 0.016 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 15 | 15 (1.000) | 64 (0.541) | infeasible (0.142) | infeasible (0.158) | 0.050 | 0.050 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 211 | 211 (1.000) | 493 (0.228) | infeasible (0.093) | infeasible (0.093) | 0.007 | 0.007 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 31 | 31 (1.000) | 61 (0.706) | infeasible (0.147) | infeasible (0.158) | 0.116 | 0.116 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 | 113 (1.000) | 122 (0.874) | infeasible (0.104) | infeasible (0.122) | 0.061 | 0.061 | – | – |

### fireworks_ai/qwen3p8-2p4t-a95b

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | lines-qwen2t r1 | lines-qwen2t-2 r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 | 139 (1.000) | 326 (0.313) | infeasible (0.165) | infeasible (0.129) | 0.000 | – | 0.000 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 282 | 282 (1.000) | 342 (0.646) | infeasible (0.141) | infeasible (0.141) | 0.153 | – | 0.153 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 282 | 282 (1.000) | 335 (0.677) | infeasible (0.059) | infeasible (0.165) | 0.129 | – | 0.129 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 292 | 292 (1.000) | 587 (0.251) | infeasible (0.141) | infeasible (0.153) | – | 0.188 | 0.188 | – | – |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4406 | 4406 (1.000) | 4683 (0.891) | infeasible (0.125) | infeasible (0.100) | – | 0.150 | 0.150 | – | – |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1759 | 1759 (1.000) | 2631 (0.318) | infeasible (0.114) | infeasible (0.100) | – | 0.086 | 0.086 | – | – |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 376 | 376 (1.000) | 407 (0.839) | infeasible (0.133) | infeasible (0.147) | 0.147 | – | 0.147 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 413 | 413 (1.000) | 539 (0.339) | infeasible (0.119) | infeasible (0.163) | 0.141 | – | 0.141 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 413 | 413 (1.000) | 661 (0.226) | infeasible (0.119) | infeasible (0.141) | 0.111 | – | 0.111 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 | 40 (1.000) | 372 (0.207) | infeasible (0.056) | infeasible (0.128) | 0.112 | – | 0.112 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 | 40 (1.000) | 292 (0.222) | infeasible (0.080) | infeasible (0.152) | 0.056 | – | 0.056 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 15 | 15 (1.000) | 64 (0.541) | infeasible (0.142) | infeasible (0.158) | 0.000 | – | 0.000 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 211 | 211 (1.000) | 493 (0.228) | infeasible (0.093) | infeasible (0.093) | 0.000 | – | 0.000 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 31 | 31 (1.000) | 61 (0.706) | infeasible (0.147) | infeasible (0.158) | 0.137 | – | 0.137 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 | 113 (1.000) | 122 (0.874) | infeasible (0.104) | infeasible (0.122) | 0.174 | – | 0.174 | – | – |

### anthropic/claude-sonnet-5-5

| Task | Weather | Tier | Ships | Watches | Hindsight | Anchor | Follower | Silent | Naive | r1 | Mean | Regret vs hindsight | Regret vs anchor |
|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0-e15 | 2025-W52 storm | busy | 17 | 6 | 139 | 139 (1.000) | 326 (0.313) | infeasible (0.165) | infeasible (0.129) | 0.176 | 0.176 | – | – |
| dock-24B-w07x1-busy-0-e04 | 2023-W44 bust | busy | 17 | 10 | 282 | 282 (1.000) | 342 (0.646) | infeasible (0.141) | infeasible (0.141) | 0.176 | 0.176 | – | – |
| dock-24B-w07x1-busy-0-e08 | 2024-W44 storm | busy | 17 | 9 | 282 | 282 (1.000) | 335 (0.677) | infeasible (0.059) | infeasible (0.165) | 0.153 | 0.153 | – | – |
| dock-24B-w07x1-busy-0-e09 | 2024-W46 storm | busy | 17 | 10 | 292 | 292 (1.000) | 587 (0.251) | infeasible (0.141) | infeasible (0.153) | 0.290 | 0.290 | 235 | 235 |
| dock-24B-w16x1-busy-0-e12 | 2025-W03 storm | busy | 16 | 10 | 4406 | 4406 (1.000) | 4683 (0.891) | infeasible (0.125) | infeasible (0.100) | 0.808 | 0.808 | 517 | 517 |
| dock-24B-w35x1-busy-0-e00 | 2023-W06 storm | busy | 14 | 10 | 1759 | 1759 (1.000) | 2631 (0.318) | infeasible (0.114) | infeasible (0.100) | 0.439 | 0.439 | 550 | 550 |
| dock-24B-w37x1-standard-0-e01 | 2023-W10 storm | standard | 15 | 5 | 376 | 376 (1.000) | 407 (0.839) | infeasible (0.133) | infeasible (0.147) | 0.147 | 0.147 | – | – |
| dock-36A-w05x1-busy-0-e09 | 2024-W46 storm | busy | 27 | 7 | 413 | 413 (1.000) | 539 (0.339) | infeasible (0.119) | infeasible (0.163) | 0.170 | 0.170 | – | – |
| dock-36A-w05x1-busy-0-e14 | 2025-W43 storm | busy | 27 | 6 | 413 | 413 (1.000) | 661 (0.226) | infeasible (0.119) | infeasible (0.141) | 0.148 | 0.148 | – | – |
| dock-36A-w06x1-busy-0-e07 | 2024-W18 storm | busy | 25 | 7 | 40 | 40 (1.000) | 372 (0.207) | infeasible (0.056) | infeasible (0.128) | 0.072 | 0.072 | – | – |
| dock-36A-w06x1-busy-0-e12 | 2025-W03 storm | busy | 25 | 9 | 40 | 40 (1.000) | 292 (0.222) | infeasible (0.080) | infeasible (0.152) | 0.176 | 0.176 | – | – |
| dock-36A-w06x1-standard-0-e07 | 2024-W18 storm | standard | 24 | 4 | 15 | 15 (1.000) | 64 (0.541) | infeasible (0.142) | infeasible (0.158) | 0.150 | 0.150 | – | – |
| dock-36A-w17x1-busy-0-e12 | 2025-W03 storm | busy | 28 | 8 | 211 | 211 (1.000) | 493 (0.228) | infeasible (0.093) | infeasible (0.093) | 0.193 | 0.193 | – | – |
| dock-36A-w35x1-standard-0-e03 | 2023-W35 storm | standard | 19 | 8 | 31 | 31 (1.000) | 61 (0.706) | infeasible (0.147) | infeasible (0.158) | 0.147 | 0.147 | – | – |
| dock-36A-w37x1-busy-0-e12 | 2025-W03 storm | busy | 23 | 8 | 113 | 113 (1.000) | 122 (0.874) | infeasible (0.104) | infeasible (0.122) | 0.174 | 0.174 | – | – |

## Unscored runs

| Sweep | Model | Task | Rep | Attempts | Last outcome | Spend |
|---|---|---|---:|---:|---|---:|
| lines-dsflash | fireworks_ai/deepseek-v4p1-flash | dock-36A-w17x1-busy-0-e12 | 1 | 3 | RuntimeError | $0.00 |
| lines-glm | fireworks_ai/glm-5p3 | dock-24B-w07x1-busy-0-e04 | 1 | 3 | RuntimeError | $0.00 |
| lines-glm | fireworks_ai/glm-5p3 | dock-24B-w16x1-busy-0-e12 | 1 | 3 | RuntimeError | $0.00 |
| lines-glm-2 | fireworks_ai/glm-5p3 | dock-24B-w07x1-busy-0-e04 | 1 | 2 | no_instance | $20.00 |
| lines-glm-2 | fireworks_ai/glm-5p3 | dock-24B-w16x1-busy-0-e12 | 1 | 1 | no_instance | $10.00 |
| lines-glmflash | fireworks_ai/glm-5p3-flash | dock-36A-w17x1-busy-0-e12 | 1 | 3 | RuntimeError | $0.00 |
| lines-glmflash | fireworks_ai/glm-5p3-flash | dock-24B-w16x1-busy-0-e12 | 1 | 3 | RuntimeError | $0.00 |
| lines-glmflash | fireworks_ai/glm-5p3-flash | dock-24B-w35x1-busy-0-e00 | 1 | 3 | RuntimeError | $0.00 |
| lines-glmflash-2 | fireworks_ai/glm-5p3-flash | dock-24B-w35x1-busy-0-e00 | 1 | 3 | no_instance | $3.00 |
| lines-gpt | openai/gpt-6.1-sol | dock-36A-w05x1-busy-0-e09 | 1 | 3 | RuntimeError | $0.00 |
| lines-kimi | fireworks_ai/kimi-k3 | dock-36A-w06x1-busy-0-e12 | 1 | 1 | cost_cap | $7.13 |
| lines-kimi-2 | fireworks_ai/kimi-k3 | dock-36A-w06x1-busy-0-e12 | 1 | 2 | no_instance | $20.00 |
| lines-opus | anthropic/claude-opus-5-5 | dock-24B-w16x1-busy-0-e12 | 1 | 3 | RuntimeError | $15.00 |
| lines-qwen2t | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w07x1-busy-0-e09 | 1 | 2 | AgentUnreachableError | $10.00 |
| lines-qwen2t | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w16x1-busy-0-e12 | 1 | 2 | interrupted | $10.00 |
| lines-qwen2t | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w35x1-busy-0-e00 | 1 | 2 | no_instance | $20.00 |

## Runs whose agent reward differs from the verifier's

Only runs whose agent saw the week end.

None.
