# PortSim live: portsim-llm on the live weeks

Sweeps: `live-pilot-sonnet` (anthropic/claude-sonnet-5-5; 2 tasks, k=1, episode cap $3.5); `live-pilot-gpt` (openai/gpt-6.1-sol; 2 tasks, k=1, episode cap $1.5); `live-sonnet` (anthropic/claude-sonnet-5-5; 13 tasks, k=1, episode cap $3.5); `live-gpt` (openai/gpt-6.1-sol; 13 tasks, k=1, episode cap $1.5).
Harness: portsim-llm. References: the rolling CP-SAT re-planner and the naive online policy, played on the same weeks (data/live/references.jsonl).

Spend: $6.80 known; 0 attempts with no spend recorded, $0.00 at the cap. Attempts: 32, retries: 2. Unscored runs: 0 of 30.

## Per model

| Model | Tasks | Runs scored/planned | Mean reward (95% CI) | Rolling reference | Naive reference | Reached done per rep | Feasible | Optimal | Mean regret | Mean excused cost | Median turns | Tokens in/out per episode | Cached tokens per episode | Cost per episode | Spend |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| anthropic/claude-sonnet-5-5 | 15 | 15/15 | 0.904 (0.854 to 0.945) | 1.000 | 0.202 | 15 | 15 | 2 | 11.200 | 0.000 | 8 | 232.4k/17.9k | 193.6k | $0.3152 | $5.85 |
| openai/gpt-6.1-sol | 15 | 15/15 | 0.957 (0.916 to 0.991) | 1.000 | 0.202 | 15 | 15 | 10 | 9.933 | 0.000 | 13 | 130.5k/2.2k | 115.8k | $0.0633 | $0.95 |

## Week by week

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

## Unscored runs

None.

## Runs whose agent reward differs from the verifier's

Only runs whose agent saw the week end.

None.
