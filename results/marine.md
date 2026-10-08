# PortSim marine: portsim-llm on the live weeks with pilots and tugs

Sweeps: `marine-pilot-sonnet` (anthropic/claude-sonnet-5-5; 2 tasks, k=1, episode cap $3.5); `marine-pilot-gpt` (openai/gpt-6.1-sol; 2 tasks, k=1, episode cap $1.5); `marine-sonnet` (anthropic/claude-sonnet-5-5; 13 tasks, k=1, episode cap $3.5); `marine-gpt` (openai/gpt-6.1-sol; 13 tasks, k=1, episode cap $1.5).
Harness: portsim-llm. References: the rolling CP-SAT re-planner and the naive online policy, played on the same weeks with pilots and tugs (data/marine/references.jsonl).

Spend: $8.32 known; 1 attempt with no spend recorded, $3.50 at the cap. Attempts: 33, retries: 3. Unscored runs: 1 of 30.

## Per model

| Model | Tasks | Runs scored/planned | Mean reward (95% CI) | Rolling reference | Naive reference | Reached done per rep | Feasible | Optimal | Mean regret | Mean excused cost | Median turns | Tokens in/out per episode | Cached tokens per episode | Cost per episode | Spend |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| anthropic/claude-sonnet-5-5 | 14 | 14/15 | 0.932 (0.886 to 0.971) | 1.000 | 0.187 | 14 | 14 | 5 | 9.714 | 0.000 | 11 | 340.3k/26.3k | 287.5k | $0.4521 | $7.06 + 1 unknown |
| openai/gpt-6.1-sol | 15 | 15/15 | 0.905 (0.790 to 0.977) | 1.000 | 0.187 | 15 | 14 | 7 | 5.643 | 0.000 | 14 | 200.3k/2.6k | 180.5k | $0.0841 | $1.26 |

## Week by week

### anthropic/claude-sonnet-5-5

| Task | Tier | Ships | Watches | Rolling (cost, reward) | Naive (cost, reward) | marine-pilot-sonnet r1 | marine-sonnet r1 | Mean |
|---|---|---:|---:|---|---|---:|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 4 | 87 (1.000) | 663 (0.200) | – | 0.944 | 0.944 |
| dock-24B-w06x1-standard-0 | standard | 16 | 4 | 114 (1.000) | 311 (0.222) | – | 0.867 | 0.867 |
| dock-24B-w07x1-busy-0 | busy | 17 | 7 | 226 (1.000) | infeasible (0.165) | 0.989 | – | 0.989 |
| dock-24B-w16x1-busy-0 | busy | 16 | 9 | 1365 (1.000) | infeasible (0.175) | – | 0.945 | 0.945 |
| dock-24B-w35x1-busy-0 | busy | 14 | 8 | 1238 (1.000) | 2941 (0.200) | – | 0.786 | 0.786 |
| dock-24B-w37x1-standard-0 | standard | 15 | 4 | 229 (1.000) | 749 (0.203) | – | 1.000 | 1.000 |
| dock-36A-w05x1-busy-0 | busy | 27 | 5 | 406 (1.000) | infeasible (0.163) | – | 1.000 | 1.000 |
| dock-36A-w06x1-busy-0 | busy | 25 | 6 | 40 (1.000) | infeasible (0.184) | – | 1.000 | 1.000 |
| dock-36A-w06x1-standard-0 | standard | 24 | 3 | 14 (1.000) | 591 (0.200) | – | 0.920 | 0.920 |
| dock-36A-w10x1-standard-0 | standard | 32 | 2 | 39 (1.000) | infeasible (0.188) | – | – | – |
| dock-36A-w15x1-standard-0 | standard | 30 | 4 | 119 (1.000) | infeasible (0.147) | – | 1.000 | 1.000 |
| dock-36A-w17x1-busy-0 | busy | 28 | 5 | 152 (1.000) | 1545 (0.200) | – | 1.000 | 1.000 |
| dock-36A-w35x1-standard-0 | standard | 19 | 5 | 10 (1.000) | infeasible (0.179) | 0.930 | – | 0.930 |
| dock-36A-w37x1-busy-0 | busy | 23 | 7 | 36 (1.000) | infeasible (0.183) | – | 0.924 | 0.924 |
| dock-36A-w37x1-standard-0 | standard | 22 | 5 | 15 (1.000) | infeasible (0.191) | – | 0.746 | 0.746 |

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

## Unscored runs

| Sweep | Model | Task | Rep | Attempts | Last outcome | Spend |
|---|---|---|---:|---:|---|---:|
| marine-sonnet | anthropic/claude-sonnet-5-5 | dock-36A-w10x1-standard-0 | 1 | 2 | interrupted | $3.50 |

## Runs whose agent reward differs from the verifier's

Only runs whose agent saw the week end.

None.
