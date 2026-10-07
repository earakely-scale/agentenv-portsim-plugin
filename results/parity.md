# PortSim parity: portsim-llm against the published dock-eval50 run

Sweeps: `g2` (openai/gpt-6.1-sol, anthropic/claude-sonnet-5-5; 10 tasks, k=1, episode cap $2).
Harness: portsim-llm. Published: dock-eval50 @ b0f4c2f, 300 episodes.

Spend: $5.19 known; 0 attempts with no spend recorded, $0.00 at the cap. Attempts: 22, retries: 2. Unscored runs: 0 of 20.

## Per model

| Model | Published as | Tasks | Runs scored/planned | Ours mean (95% CI) | Published mean on these tasks (95% CI) | Mean diff ours−published (95% CI) | Submitted per rep / published | Feasible | Optimal | Median turns ours/published | Tokens in/out per episode ours/published | Cost per episode | Spend |
|---|---|---:|---:|---|---|---|---:|---:|---:|---:|---|---:|---:|
| openai/gpt-6.1-sol | openai:gpt-6.1-sol | 10 | 10/10 | 0.907 (0.777 to 0.998) | 0.872 (0.748 to 0.988) | +0.035 (-0.000 to +0.097) | 10 / 10 | 10 / 10 | 7 / 5 | 3 / 3 | 30.3k/6.7k vs 29.4k/6.6k | $0.0922 | $0.92 |
| anthropic/claude-sonnet-5-5 | anthropic:claude-sonnet-5-5 | 10 | 10/10 | 0.778 (0.566 to 0.946) | 0.839 (0.677 to 0.959) | -0.061 (-0.143 to +0.003) | 9 / 10 | 9 / 10 | 3 / 3 | 2 / 2.5 | 48.1k/26.2k vs 107.2k/30.4k | $0.3578 | $4.27 |

## Per tier

Mean reward over each tier's tasks, ours / published.

| Model | standard | busy | storm | extreme |
|---|---:|---:|---:|---:|
| openai/gpt-6.1-sol | 1.000 / 1.000 | 0.830 / 0.830 | 0.860 / 0.843 | 1.000 / 0.850 |
| anthropic/claude-sonnet-5-5 | 0.944 / 0.968 | 0.782 / 0.786 | 0.606 / 0.725 | 0.866 / 0.961 |

## Week by week

### openai/gpt-6.1-sol

| Task | Tier | Ships | Published (reward, end, turns) | r1 | Ours mean | Diff |
|---|---|---:|---|---:|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 1.000 (submitted, 2) | 1.000 | 1.000 | +0.000 |
| dock-24B-w06x2-storm-0 | storm | 32 | 0.957 (submitted, 3) | 1.000 | 1.000 | +0.043 |
| dock-24B-w35x2-extreme-1 | extreme | 25 | 1.000 (submitted, 3) | 1.000 | 1.000 | +0.000 |
| dock-24B-w35x2-storm-0 | storm | 24 | 0.981 (submitted, 3) | 0.976 | 0.976 | -0.005 |
| dock-36A-w05x1-busy-0 | busy | 27 | 1.000 (submitted, 3) | 1.000 | 1.000 | +0.000 |
| dock-36A-w05x2-busy-0 | busy | 51 | 0.489 (submitted, 3) | 0.489 | 0.489 | +0.000 |
| dock-36A-w15x2-storm-0 | storm | 56 | 0.591 (submitted, 6) | 0.605 | 0.605 | +0.014 |
| dock-36A-w17x1-standard-0 | standard | 29 | 1.000 (submitted, 3) | 1.000 | 1.000 | +0.000 |
| dock-36A-w35x1-standard-0 | standard | 19 | 1.000 (submitted, 3) | 1.000 | 1.000 | +0.000 |
| dock-36A-w35x2-extreme-0 | extreme | 39 | 0.700 (submitted, 4) | 1.000 | 1.000 | +0.300 |

### anthropic/claude-sonnet-5-5

| Task | Tier | Ships | Published (reward, end, turns) | r1 | Ours mean | Diff |
|---|---|---:|---|---:|---:|---:|
| dock-24B-w06x1-busy-0 | busy | 17 | 0.944 (submitted, 2) | 0.944 | 0.944 | +0.000 |
| dock-24B-w06x2-storm-0 | storm | 32 | 0.878 (submitted, 2) | 0.842 | 0.842 | -0.036 |
| dock-24B-w35x2-extreme-1 | extreme | 25 | 1.000 (submitted, 3) | 1.000 | 1.000 | +0.000 |
| dock-24B-w35x2-storm-0 | storm | 24 | 0.918 (submitted, 2) | 0.976 | 0.976 | +0.058 |
| dock-36A-w05x1-busy-0 | busy | 27 | 1.000 (submitted, 3) | 1.000 | 1.000 | +0.000 |
| dock-36A-w05x2-busy-0 | busy | 51 | 0.412 (submitted, 4) | 0.401 | 0.401 | -0.011 |
| dock-36A-w15x2-storm-0 | storm | 56 | 0.379 (submitted, 8) | 0.000 | 0.000 | -0.379 |
| dock-36A-w17x1-standard-0 | standard | 29 | 0.936 (submitted, 2) | 0.889 | 0.889 | -0.047 |
| dock-36A-w35x1-standard-0 | standard | 19 | 1.000 (submitted, 2) | 1.000 | 1.000 | +0.000 |
| dock-36A-w35x2-extreme-0 | extreme | 39 | 0.922 (submitted, 4) | 0.732 | 0.732 | -0.190 |

## Unscored runs

None.

## Runs whose agent reward differs from the verifier's

None.
