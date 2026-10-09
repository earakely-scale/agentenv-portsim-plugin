# PortSim marine: portsim-llm on the live weeks with pilots and tugs

Sweeps: `marine-pilot-gpt` (openai/gpt-6.1-sol; 2 tasks, k=1, episode cap $1.5); `marine-gpt` (openai/gpt-6.1-sol; 13 tasks, k=1, episode cap $1.5); `marine-pilot-sonnet` (anthropic/claude-sonnet-5-5; 2 tasks, k=1, episode cap $3.5); `marine-sonnet` (anthropic/claude-sonnet-5-5; 13 tasks, k=1, episode cap $3.5); `marine-sonnet-2` (anthropic/claude-sonnet-5-5; 1 tasks, k=1, episode cap $3.5); `marine-opus` (anthropic/claude-opus-5-5; 15 tasks, k=1, episode cap $8); `marine-haiku` (anthropic/claude-haiku-5-5; 15 tasks, k=1, episode cap $2); `marine-astra` (openai/gpt-6-astra; 15 tasks, k=1, episode cap $8); `marine-luna` (openai/gpt-6-luna; 15 tasks, k=1, episode cap $2); `marine-kimi` (fireworks_ai/kimi-k3; 15 tasks, k=1, episode cap $12); `marine-glm` (fireworks_ai/glm-5p3; 15 tasks, k=1, episode cap $4); `marine-glmflash` (fireworks_ai/glm-5p3-flash; 15 tasks, k=1, episode cap $2); `marine-qwen2t` (fireworks_ai/qwen3p8-2p4t-a95b; 15 tasks, k=1, episode cap $5); `marine-qwen27b` (groq/qwen/qwen3.8-27b; 15 tasks, k=1, episode cap $4); `marine-dsflash` (fireworks_ai/deepseek-v4p1-flash; 15 tasks, k=1, episode cap $2).
Harness: portsim-llm. References: the rolling CP-SAT re-planner and the naive online policy, played on the same weeks with pilots and tugs (data/marine/references.jsonl).

Spend: $81.44 known; 1 attempt with no spend recorded, $3.50 at the cap. Attempts: 204, retries: 23. Unscored runs: 1 of 181.

## Per model

| Model | Tasks | Runs scored/planned | Mean reward (95% CI) | Rolling reference | Naive reference | Reached done per rep | Feasible | Optimal | Mean regret | Mean excused cost | Median turns | Tokens in/out per episode | Cached tokens per episode | Cost per episode | Spend |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| openai/gpt-6.1-sol | 15 | 15/15 | 0.905 (0.790 to 0.977) | 1.000 | 0.187 | 15 | 14 | 7 | 5.643 | 0.000 | 14 | 200.3k/2.6k | 180.5k | $0.0841 | $1.26 |
| anthropic/claude-sonnet-5-5 | 15 | 15/16 | 0.932 (0.892 to 0.967) | 1.000 | 0.187 | 15 | 15 | 5 | 9.400 | 0.000 | 11 | 326.0k/26.2k | 274.0k | $0.4465 | $7.43 + 1 unknown |
| anthropic/claude-opus-5-5 | 15 | 15/15 | 0.951 (0.914 to 0.983) | 1.000 | 0.187 | 15 | 15 | 8 | 5.600 | 0.000 | 11 | 298.2k/13.1k | 258.3k | $0.5641 | $8.46 |
| anthropic/claude-haiku-5-5 | 15 | 15/15 | 0.639 (0.507 to 0.765) | 1.000 | 0.187 | 15 | 15 | 0 | 99.467 | 0.000 | 12 | 558.0k/38.7k | 485.6k | $0.0374 | $0.56 |
| openai/gpt-6-astra | 15 | 15/15 | 0.956 (0.910 to 0.993) | 1.000 | 0.187 | 15 | 15 | 10 | 9.467 | 0.000 | 17 | 231.9k/2.5k | 212.2k | $0.5345 | $8.02 |
| openai/gpt-6-luna | 15 | 15/15 | 0.287 (0.199 to 0.407) | 1.000 | 0.187 | 15 | 11 | 0 | 4549.636 | 15.467 | 19 | 633.6k/25.9k | 584.9k | $0.0237 | $0.36 |
| fireworks_ai/kimi-k3 | 15 | 15/15 | 0.446 (0.256 to 0.636) | 1.000 | 0.187 | 15 | 6 | 0 | 8.333 | 0.000 | 16 | 249.7k/42.4k | 220.3k | $1.2791 | $19.19 |
| fireworks_ai/glm-5p3 | 15 | 15/15 | 0.593 (0.368 to 0.804) | 1.000 | 0.187 | 11 | 10 | 3 | 36.100 | 0.000 | 18 | 236.5k/84.1k | 204.7k | $0.4676 | $7.01 |
| fireworks_ai/glm-5p3-flash | 15 | 15/15 | 0.461 (0.299 to 0.652) | 1.000 | 0.187 | 15 | 6 | 3 | 8.833 | 0.000 | 14 | 278.2k/103.7k | 230.2k | $0.0659 | $0.99 |
| fireworks_ai/qwen3p8-2p4t-a95b | 15 | 15/15 | 0.519 (0.296 to 0.746) | 1.000 | 0.187 | 12 | 7 | 5 | 2.286 | 0.000 | 15 | 300.1k/117.2k | 272.3k | $0.8272 | $12.41 |
| groq/qwen/qwen3.8-27b | 15 | 15/15 | 0.073 (0.047 to 0.100) | 1.000 | 0.187 | 15 | 0 | 0 | – | 0.000 | 24 | 892.1k/24.4k | 0.0k | $0.8111 | $12.17 |
| fireworks_ai/deepseek-v4p1-flash | 15 | 15/15 | 0.598 (0.392 to 0.786) | 1.000 | 0.187 | 12 | 9 | 2 | 6.556 | 0.000 | 19 | 403.1k/141.0k | 368.3k | $0.2394 | $3.59 |

## Week by week

### openai/gpt-6.1-sol

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | marine-pilot-gpt r1 | marine-gpt r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | – | 0.913 | 0.913 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | – | 0.930 | 0.930 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | 1.000 | – | 1.000 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1365 (1.000) | infeasible (0.175) | – | 0.925 | 0.925 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1238 (1.000) | 2941 (0.200) | – | 0.171 | 0.171 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | – | 1.000 | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 406 (1.000) | infeasible (0.163) | – | 1.000 | 1.000 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | infeasible (0.184) | – | 0.914 | 0.914 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | – | 0.986 | 0.986 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | infeasible (0.188) | – | 1.000 | 1.000 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | infeasible (0.147) | – | 1.000 | 1.000 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | – | 1.000 | 1.000 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 0.930 | – | 0.930 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | infeasible (0.183) | – | 1.000 | 1.000 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | infeasible (0.191) | – | 0.806 | 0.806 |

### anthropic/claude-sonnet-5-5

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | marine-pilot-sonnet r1 | marine-sonnet r1 | marine-sonnet-2 r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | – | 0.944 | – | 0.944 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | – | 0.867 | – | 0.867 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | 0.989 | – | – | 0.989 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1365 (1.000) | infeasible (0.175) | – | 0.945 | – | 0.945 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1238 (1.000) | 2941 (0.200) | – | 0.786 | – | 0.786 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | – | 1.000 | – | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 406 (1.000) | infeasible (0.163) | – | 1.000 | – | 1.000 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | infeasible (0.184) | – | 1.000 | – | 1.000 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | – | 0.920 | – | 0.920 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | infeasible (0.188) | – | – | 0.933 | 0.933 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | infeasible (0.147) | – | 1.000 | – | 1.000 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | – | 1.000 | – | 1.000 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 0.930 | – | – | 0.930 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | infeasible (0.183) | – | 0.924 | – | 0.924 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | infeasible (0.191) | – | 0.746 | – | 0.746 |

### anthropic/claude-opus-5-5

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 1.000 | 1.000 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 1.000 | 1.000 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | 0.900 | 0.900 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1365 (1.000) | infeasible (0.175) | 1.000 | 1.000 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1238 (1.000) | 2941 (0.200) | 0.866 | 0.866 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 1.000 | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 406 (1.000) | infeasible (0.163) | 1.000 | 1.000 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | infeasible (0.184) | 0.945 | 0.945 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.986 | 0.986 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | infeasible (0.188) | 1.000 | 1.000 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | infeasible (0.147) | 0.816 | 0.816 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.944 | 0.944 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 1.000 | 1.000 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | infeasible (0.183) | 1.000 | 1.000 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | infeasible (0.191) | 0.806 | 0.806 |

### anthropic/claude-haiku-5-5

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.210 | 0.210 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 0.930 | 0.930 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | 0.938 | 0.938 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1365 (1.000) | infeasible (0.175) | 0.793 | 0.793 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1238 (1.000) | 2941 (0.200) | 0.547 | 0.547 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 0.687 | 0.687 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 406 (1.000) | infeasible (0.163) | 0.621 | 0.621 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | infeasible (0.184) | 0.525 | 0.525 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.294 | 0.294 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | infeasible (0.188) | 0.421 | 0.421 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | infeasible (0.147) | 0.200 | 0.200 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.756 | 0.756 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 0.930 | 0.930 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | infeasible (0.183) | 0.924 | 0.924 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | infeasible (0.191) | 0.806 | 0.806 |

### openai/gpt-6-astra

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.913 | 0.913 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 1.000 | 1.000 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | 1.000 | 1.000 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1365 (1.000) | infeasible (0.175) | 0.925 | 0.925 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1238 (1.000) | 2941 (0.200) | 0.709 | 0.709 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 1.000 | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 406 (1.000) | infeasible (0.163) | 1.000 | 1.000 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | infeasible (0.184) | 1.000 | 1.000 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.986 | 0.986 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | infeasible (0.188) | 1.000 | 1.000 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | infeasible (0.147) | 1.000 | 1.000 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 1.000 | 1.000 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 1.000 | 1.000 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | infeasible (0.183) | 1.000 | 1.000 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | infeasible (0.191) | 0.806 | 0.806 |

### openai/gpt-6-luna

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.176 | 0.176 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 0.188 | 0.188 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | 0.200 | 0.200 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1365 (1.000) | infeasible (0.175) | 0.647 | 0.647 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1238 (1.000) | 2941 (0.200) | 0.368 | 0.368 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 0.212 | 0.212 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 406 (1.000) | infeasible (0.163) | 0.258 | 0.258 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | infeasible (0.184) | 0.200 | 0.200 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.167 | 0.167 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | infeasible (0.188) | 0.200 | 0.200 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | infeasible (0.147) | 0.167 | 0.167 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.200 | 0.200 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 0.200 | 0.200 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | infeasible (0.183) | 0.924 | 0.924 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | infeasible (0.191) | 0.200 | 0.200 |

### fireworks_ai/kimi-k3

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.129 | 0.129 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 0.930 | 0.930 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | 0.165 | 0.165 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1365 (1.000) | infeasible (0.175) | 0.100 | 0.100 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1238 (1.000) | 2941 (0.200) | 0.086 | 0.086 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 0.160 | 0.160 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 406 (1.000) | infeasible (0.163) | 0.944 | 0.944 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | infeasible (0.184) | 0.168 | 0.168 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.920 | 0.920 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | infeasible (0.188) | 0.872 | 0.872 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | infeasible (0.147) | 0.180 | 0.180 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.179 | 0.179 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 0.147 | 0.147 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | infeasible (0.183) | 0.938 | 0.938 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | infeasible (0.191) | 0.765 | 0.765 |

### fireworks_ai/glm-5p3

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.165 | 0.165 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 0.203 | 0.203 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | 0.890 | 0.890 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1365 (1.000) | infeasible (0.175) | 0.000 | 0.000 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1238 (1.000) | 2941 (0.200) | 0.100 | 0.100 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 1.000 | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 406 (1.000) | infeasible (0.163) | 0.944 | 0.944 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | infeasible (0.184) | 1.000 | 1.000 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.986 | 0.986 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | infeasible (0.188) | 0.000 | 0.000 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | infeasible (0.147) | 0.000 | 0.000 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.867 | 0.867 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 0.930 | 0.930 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | infeasible (0.183) | 1.000 | 1.000 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | infeasible (0.191) | 0.806 | 0.806 |

### fireworks_ai/glm-5p3-flash

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.165 | 0.165 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 1.000 | 1.000 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | 0.803 | 0.803 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1365 (1.000) | infeasible (0.175) | 0.175 | 0.175 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1238 (1.000) | 2941 (0.200) | 0.186 | 0.186 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 1.000 | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 406 (1.000) | infeasible (0.163) | 0.163 | 0.163 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | infeasible (0.184) | 0.128 | 0.128 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.860 | 0.860 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | infeasible (0.188) | 0.755 | 0.755 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | infeasible (0.147) | 0.147 | 0.147 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.171 | 0.171 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 0.189 | 0.189 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | infeasible (0.183) | 1.000 | 1.000 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | infeasible (0.191) | 0.173 | 0.173 |

### fireworks_ai/qwen3p8-2p4t-a95b

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.153 | 0.153 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 0.163 | 0.163 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | 1.000 | 1.000 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1365 (1.000) | infeasible (0.175) | 0.175 | 0.175 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1238 (1.000) | 2941 (0.200) | 0.100 | 0.100 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 1.000 | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 406 (1.000) | infeasible (0.163) | 1.000 | 1.000 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | infeasible (0.184) | 0.884 | 0.884 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.000 | 0.000 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | infeasible (0.188) | 0.194 | 0.194 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | infeasible (0.147) | 0.000 | 0.000 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.930 | 0.930 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 1.000 | 1.000 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | infeasible (0.183) | 1.000 | 1.000 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | infeasible (0.191) | 0.191 | 0.191 |

### groq/qwen/qwen3.8-27b

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.153 | 0.153 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 0.113 | 0.113 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | 0.153 | 0.153 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1365 (1.000) | infeasible (0.175) | 0.062 | 0.062 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1238 (1.000) | 2941 (0.200) | 0.014 | 0.014 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 0.080 | 0.080 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 406 (1.000) | infeasible (0.163) | 0.022 | 0.022 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | infeasible (0.184) | 0.136 | 0.136 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.133 | 0.133 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | infeasible (0.188) | 0.000 | 0.000 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | infeasible (0.147) | 0.007 | 0.007 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.050 | 0.050 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 0.063 | 0.063 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | infeasible (0.183) | 0.017 | 0.017 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | infeasible (0.191) | 0.091 | 0.091 |

### fireworks_ai/deepseek-v4p1-flash

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | 0.165 | 0.165 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | 1.000 | 1.000 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | 0.948 | 0.948 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1365 (1.000) | infeasible (0.175) | 0.175 | 0.175 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1238 (1.000) | 2941 (0.200) | 0.157 | 0.157 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | 1.000 | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 406 (1.000) | infeasible (0.163) | 0.163 | 0.163 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | infeasible (0.184) | 0.760 | 0.760 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | 0.000 | 0.000 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | infeasible (0.188) | 0.933 | 0.933 |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | infeasible (0.147) | 0.000 | 0.000 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | 0.930 | 0.930 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 0.930 | 0.930 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | infeasible (0.183) | 0.924 | 0.924 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | infeasible (0.191) | 0.884 | 0.884 |

## Unscored runs

| Sweep | Model | Task | Rep | Attempts | Last outcome | Spend |
|---|---|---|---:|---:|---|---:|
| marine-sonnet | anthropic/claude-sonnet-5-5 | dock-36A-w10x1-standard-0 | 1 | 2 | interrupted | $3.50 |

## Runs whose agent reward differs from the verifier's

Only runs whose agent saw the week end.

None.
