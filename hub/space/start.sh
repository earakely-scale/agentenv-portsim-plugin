set -e
[ -d results/runs ] || hf download earakely-scale/PortSimEnv-AgentEnv --repo-type dataset --revision v0.4.2 --include "runs/*" \
    --local-dir results --quiet
exec agent-env portsim view --host 0.0.0.0 --port 7860
