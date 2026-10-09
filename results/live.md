# PortSim live: portsim-llm on the live weeks

Sweeps: `live-pilot-gpt` (openai/gpt-6.1-sol; 2 tasks, k=1, episode cap $1.5); `live-gpt` (openai/gpt-6.1-sol; 13 tasks, k=1, episode cap $1.5); `live-pilot-sonnet` (anthropic/claude-sonnet-5-5; 2 tasks, k=1, episode cap $3.5); `live-sonnet` (anthropic/claude-sonnet-5-5; 13 tasks, k=1, episode cap $3.5); `live-opus` (anthropic/claude-opus-5-5; 15 tasks, k=1, episode cap $8); `live-opus-2` (anthropic/claude-opus-5-5; 3 tasks, k=1, episode cap $8); `live-haiku` (anthropic/claude-haiku-5-5; 15 tasks, k=1, episode cap $2); `live-astra` (openai/gpt-6-astra; 15 tasks, k=1, episode cap $8); `live-luna` (openai/gpt-6-luna; 15 tasks, k=1, episode cap $2); `live-kimi` (fireworks_ai/kimi-k3; 15 tasks, k=1, episode cap $12); `live-glm` (fireworks_ai/glm-5p3; 15 tasks, k=1, episode cap $4); `live-glmflash` (fireworks_ai/glm-5p3-flash; 15 tasks, k=1, episode cap $2); `live-qwen2t` (fireworks_ai/qwen3p8-2p4t-a95b; 15 tasks, k=1, episode cap $5); `live-qwen2t-2` (fireworks_ai/qwen3p8-2p4t-a95b; 1 tasks, k=1, episode cap $10); `live-qwen2t-3` (fireworks_ai/qwen3p8-2p4t-a95b; 1 tasks, k=1, episode cap $10); `live-qwen27b` (groq/qwen/qwen3.8-27b; 15 tasks, k=1, episode cap $4); `live-dsflash` (fireworks_ai/deepseek-v4p1-flash; 15 tasks, k=1, episode cap $2).
Harness: portsim-llm. References: the rolling CP-SAT re-planner and the naive online policy, played on the same weeks (data/live/references.jsonl).

Spend: $68.36 known; 20 attempts with no spend recorded, $78.00 at the cap. Attempts: 268, retries: 83. Unscored runs: 5 of 185.

## Per model

| Model | Tasks | Runs scored/planned | Mean reward (95% CI) | Rolling reference | Naive reference | Reached done per rep | Feasible | Optimal | Mean regret | Mean excused cost | Median turns | Tokens in/out per episode | Cached tokens per episode | Cost per episode | Spend |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| openai/gpt-6.1-sol | 15 | 15/15 | 0.957 (0.916 to 0.991) | 1.000 | 0.202 | 15 | 15 | 10 | 9.933 | 0.000 | 13 | 130.5k/2.2k | 115.8k | $0.0633 | $0.95 |
| anthropic/claude-sonnet-5-5 | 15 | 15/15 | 0.904 (0.854 to 0.945) | 1.000 | 0.202 | 15 | 15 | 2 | 11.200 | 0.000 | 8 | 232.4k/17.9k | 193.6k | $0.3152 | $5.85 |
| anthropic/claude-opus-5-5 | 15 | 15/18 | 0.976 (0.954 to 0.993) | 1.000 | 0.202 | 15 | 15 | 10 | 3.933 | 0.000 | 10 | 201.2k/10.2k | 169.8k | $0.4296 | $6.44 + 2 unknown |
| anthropic/claude-haiku-5-5 | 15 | 15/15 | 0.694 (0.550 to 0.821) | 1.000 | 0.202 | 15 | 15 | 0 | 63.933 | 0.000 | 10 | 372.9k/31.4k | 319.4k | $0.0256 | $0.38 + 3 unknown |
| openai/gpt-6-astra | 15 | 15/15 | 0.984 (0.965 to 0.998) | 1.000 | 0.202 | 15 | 15 | 11 | 3.467 | 0.000 | 15 | 165.2k/2.0k | 150.9k | $0.3955 | $5.93 + 3 unknown |
| openai/gpt-6-luna | 15 | 15/15 | 0.335 (0.231 to 0.466) | 1.000 | 0.202 | 15 | 12 | 1 | 307.583 | 0.000 | 18 | 433.9k/18.5k | 400.6k | $0.0166 | $0.25 + 3 unknown |
| fireworks_ai/kimi-k3 | 15 | 15/15 | 0.465 (0.290 to 0.654) | 1.000 | 0.202 | 15 | 7 | 2 | 33.714 | 0.000 | 14 | 186.5k/39.6k | 166.5k | $1.0289 | $15.43 |
| fireworks_ai/glm-5p3 | 15 | 15/15 | 0.748 (0.563 to 0.920) | 1.000 | 0.202 | 14 | 11 | 5 | 2.818 | 0.000 | 18 | 233.5k/79.8k | 207.4k | $0.4415 | $6.62 |
| fireworks_ai/glm-5p3-flash | 15 | 15/15 | 0.470 (0.307 to 0.648) | 1.000 | 0.202 | 15 | 7 | 1 | 19.571 | 0.000 | 14 | 188.4k/56.9k | 147.2k | $0.0390 | $0.59 + 4 unknown |
| fireworks_ai/qwen3p8-2p4t-a95b | 15 | 15/17 | 0.686 (0.484 to 0.856) | 1.000 | 0.202 | 14 | 11 | 5 | 29.818 | 0.000 | 18 | 261.7k/98.2k | 238.7k | $0.8334 | $16.41 + 1 unknown |
| groq/qwen/qwen3.8-27b | 15 | 15/15 | 0.055 (0.037 to 0.077) | 1.000 | 0.202 | 15 | 0 | 0 | – | 1.333 | 21 | 528.5k/10.6k | 0.0k | $0.4887 | $7.33 |
| fireworks_ai/deepseek-v4p1-flash | 15 | 15/15 | 0.754 (0.573 to 0.913) | 1.000 | 0.202 | 14 | 12 | 3 | 10.167 | 0.000 | 16 | 270.2k/101.3k | 241.9k | $0.1449 | $2.17 + 4 unknown |

## Week by week

### openai/gpt-6.1-sol

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | live-pilot-gpt r1 | live-gpt r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | – | 1.000 | 1.000 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | – | 1.000 | 1.000 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | 693 (0.202) | 1.000 | – | 1.000 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1349 (1.000) | 4089 (0.200) | – | 0.870 | 0.870 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1223 (1.000) | 2941 (0.200) | – | 0.745 | 0.745 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | – | 1.000 | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 404 (1.000) | 791 (0.203) | – | 1.000 | 1.000 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | 1065 (0.200) | – | 1.000 | 1.000 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | – | 0.986 | 0.986 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | 628 (0.200) | – | 1.000 | 1.000 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | 2623 (0.200) | – | 0.872 | 0.872 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | – | 1.000 | 1.000 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | 274 (0.207) | 1.000 | – | 1.000 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | 598 (0.200) | – | 1.000 | 1.000 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | 429 (0.201) | – | 0.884 | 0.884 |

### anthropic/claude-sonnet-5-5

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | live-pilot-sonnet r1 | live-sonnet r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | – | 0.944 | 0.944 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | – | 1.000 | 1.000 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | 693 (0.202) | 0.989 | – | 0.989 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1349 (1.000) | 4089 (0.200) | – | 0.952 | 0.952 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1223 (1.000) | 2941 (0.200) | – | 0.921 | 0.921 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | – | 0.714 | 0.714 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 404 (1.000) | 791 (0.203) | – | 1.000 | 1.000 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | 1065 (0.200) | – | 0.760 | 0.760 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | – | 0.986 | 0.986 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | 628 (0.200) | – | 0.933 | 0.933 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | 2623 (0.200) | – | 0.872 | 0.872 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | – | 0.756 | 0.756 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | 274 (0.207) | 0.930 | – | 0.930 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | 598 (0.200) | – | 0.924 | 0.924 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | 429 (0.201) | – | 0.872 | 0.872 |

### anthropic/claude-opus-5-5

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | live-opus r1 | live-opus-2 r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.913 | – | 0.913 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | – | 0.930 | 0.930 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | 693 (0.202) | 1.000 | – | 1.000 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1349 (1.000) | 4089 (0.200) | 0.965 | – | 0.965 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1223 (1.000) | 2941 (0.200) | 0.892 | – | 0.892 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | – | 1.000 | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 404 (1.000) | 791 (0.203) | 1.000 | – | 1.000 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | 1065 (0.200) | 1.000 | – | 1.000 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 1.000 | – | 1.000 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | 628 (0.200) | 0.933 | – | 0.933 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | 2623 (0.200) | 1.000 | – | 1.000 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | – | 1.000 | 1.000 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | 274 (0.207) | 1.000 | – | 1.000 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | 598 (0.200) | 1.000 | – | 1.000 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | 429 (0.201) | 1.000 | – | 1.000 |

### anthropic/claude-haiku-5-5

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.206 | 0.206 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 0.930 | 0.930 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | 693 (0.202) | 0.989 | 0.989 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1349 (1.000) | 4089 (0.200) | 0.835 | 0.835 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1223 (1.000) | 2941 (0.200) | 0.802 | 0.802 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 0.493 | 0.493 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 404 (1.000) | 791 (0.203) | 0.911 | 0.911 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | 1065 (0.200) | 0.366 | 0.366 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.289 | 0.289 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | 628 (0.200) | 0.872 | 0.872 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | 2623 (0.200) | 0.386 | 0.386 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.809 | 0.809 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | 274 (0.207) | 0.708 | 0.708 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | 598 (0.200) | 0.924 | 0.924 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | 429 (0.201) | 0.884 | 0.884 |

### openai/gpt-6-astra

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 1.000 | 1.000 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 1.000 | 1.000 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | 693 (0.202) | 1.000 | 1.000 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1349 (1.000) | 4089 (0.200) | 0.927 | 0.927 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1223 (1.000) | 2941 (0.200) | 0.964 | 0.964 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 1.000 | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 404 (1.000) | 791 (0.203) | 1.000 | 1.000 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | 1065 (0.200) | 1.000 | 1.000 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.986 | 0.986 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | 628 (0.200) | 1.000 | 1.000 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | 2623 (0.200) | 1.000 | 1.000 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 1.000 | 1.000 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | 274 (0.207) | 1.000 | 1.000 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | 598 (0.200) | 1.000 | 1.000 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | 429 (0.201) | 0.884 | 0.884 |

### openai/gpt-6-luna

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.201 | 0.201 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 0.201 | 0.201 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | 693 (0.202) | 0.603 | 0.603 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1349 (1.000) | 4089 (0.200) | 0.620 | 0.620 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1223 (1.000) | 2941 (0.200) | 0.214 | 0.214 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 0.493 | 0.493 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 404 (1.000) | 791 (0.203) | 0.329 | 0.329 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | 1065 (0.200) | 0.214 | 0.214 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.150 | 0.150 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | 628 (0.200) | 0.144 | 0.144 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | 2623 (0.200) | 0.173 | 0.173 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.226 | 0.226 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | 274 (0.207) | 0.200 | 0.200 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | 598 (0.200) | 1.000 | 1.000 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | 429 (0.201) | 0.257 | 0.257 |

### fireworks_ai/kimi-k3

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.176 | 0.176 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 0.930 | 0.930 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | 693 (0.202) | 0.165 | 0.165 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1349 (1.000) | 4089 (0.200) | 0.113 | 0.113 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1223 (1.000) | 2941 (0.200) | 0.533 | 0.533 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 1.000 | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 404 (1.000) | 791 (0.203) | 0.163 | 0.163 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | 1065 (0.200) | 0.144 | 0.144 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.167 | 0.167 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | 628 (0.200) | 0.188 | 0.188 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | 2623 (0.200) | 0.933 | 0.933 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.171 | 0.171 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | 274 (0.207) | 0.469 | 0.469 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | 598 (0.200) | 1.000 | 1.000 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | 429 (0.201) | 0.816 | 0.816 |

### fireworks_ai/glm-5p3

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.944 | 0.944 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 0.188 | 0.188 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | 693 (0.202) | 0.938 | 0.938 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1349 (1.000) | 4089 (0.200) | 0.150 | 0.150 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1223 (1.000) | 2941 (0.200) | 0.100 | 0.100 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 1.000 | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 404 (1.000) | 791 (0.203) | 1.000 | 1.000 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | 1065 (0.200) | 0.168 | 0.168 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.986 | 0.986 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | 628 (0.200) | 0.933 | 0.933 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | 2623 (0.200) | 1.000 | 1.000 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 1.000 | 1.000 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | 274 (0.207) | 1.000 | 1.000 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | 598 (0.200) | 0.924 | 0.924 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | 429 (0.201) | 0.884 | 0.884 |

### fireworks_ai/glm-5p3-flash

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.141 | 0.141 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 0.608 | 0.608 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | 693 (0.202) | 0.176 | 0.176 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1349 (1.000) | 4089 (0.200) | 0.188 | 0.188 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1223 (1.000) | 2941 (0.200) | 0.143 | 0.143 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 0.687 | 0.687 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 404 (1.000) | 791 (0.203) | 1.000 | 1.000 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | 1065 (0.200) | 0.685 | 0.685 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.150 | 0.150 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | 628 (0.200) | 0.933 | 0.933 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | 2623 (0.200) | 0.187 | 0.187 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.164 | 0.164 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | 274 (0.207) | 0.179 | 0.179 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | 598 (0.200) | 0.924 | 0.924 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | 429 (0.201) | 0.884 | 0.884 |

### fireworks_ai/qwen3p8-2p4t-a95b

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | live-qwen2t r1 | live-qwen2t-2 r1 | live-qwen2t-3 r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.631 | – | – | 0.631 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 1.000 | – | – | 1.000 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | 693 (0.202) | 1.000 | – | – | 1.000 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1349 (1.000) | 4089 (0.200) | – | – | 0.909 | 0.909 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1223 (1.000) | 2941 (0.200) | 0.414 | – | – | 0.414 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 1.000 | – | – | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 404 (1.000) | 791 (0.203) | 1.000 | – | – | 1.000 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | 1065 (0.200) | 1.000 | – | – | 1.000 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.167 | – | – | 0.167 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | 628 (0.200) | 0.933 | – | – | 0.933 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | 2623 (0.200) | 0.000 | – | – | 0.000 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.193 | – | – | 0.193 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | 274 (0.207) | 0.930 | – | – | 0.930 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | 598 (0.200) | 0.924 | – | – | 0.924 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | 429 (0.201) | 0.191 | – | – | 0.191 |

### groq/qwen/qwen3.8-27b

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.094 | 0.094 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 0.075 | 0.075 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | 693 (0.202) | 0.071 | 0.071 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1349 (1.000) | 4089 (0.200) | 0.037 | 0.037 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1223 (1.000) | 2941 (0.200) | 0.043 | 0.043 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 0.067 | 0.067 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 404 (1.000) | 791 (0.203) | 0.044 | 0.044 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | 1065 (0.200) | 0.024 | 0.024 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.008 | 0.008 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | 628 (0.200) | 0.031 | 0.031 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | 2623 (0.200) | 0.027 | 0.027 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.036 | 0.036 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | 274 (0.207) | 0.137 | 0.137 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | 598 (0.200) | 0.009 | 0.009 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | 429 (0.201) | 0.127 | 0.127 |

### fireworks_ai/deepseek-v4p1-flash

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.153 | 0.153 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 1.000 | 1.000 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | 693 (0.202) | 0.948 | 0.948 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1349 (1.000) | 4089 (0.200) | 0.000 | 0.000 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1223 (1.000) | 2941 (0.200) | 0.921 | 0.921 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 0.601 | 0.601 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 404 (1.000) | 791 (0.203) | 1.000 | 1.000 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | 1065 (0.200) | 0.160 | 0.160 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.986 | 0.986 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | 628 (0.200) | 0.933 | 0.933 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | 2623 (0.200) | 0.933 | 0.933 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.867 | 0.867 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | 274 (0.207) | 0.930 | 0.930 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | 598 (0.200) | 1.000 | 1.000 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | 429 (0.201) | 0.884 | 0.884 |

## Unscored runs

| Sweep | Model | Task | Rep | Attempts | Last outcome | Spend |
|---|---|---|---:|---:|---|---:|
| live-opus | anthropic/claude-opus-5-5 | dock-36A-w17x1-busy-0 | 1 | 3 | RuntimeError | $0.00 |
| live-opus | anthropic/claude-opus-5-5 | dock-24B-w06x1-standard-0 | 1 | 3 | RuntimeError | $8.00 |
| live-opus | anthropic/claude-opus-5-5 | dock-24B-w37x1-standard-0 | 1 | 3 | RuntimeError | $0.00 |
| live-qwen2t | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w16x1-busy-0 | 1 | 1 | cost_cap | $3.91 |
| live-qwen2t-2 | fireworks_ai/qwen3p8-2p4t-a95b | dock-24B-w16x1-busy-0 | 1 | 3 | RuntimeError | $10.00 |

## Runs whose agent reward differs from the verifier's

Only runs whose agent saw the week end.

None.
