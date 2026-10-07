# Security

Please report a vulnerability privately, through GitHub's
[private vulnerability reporting](https://github.com/earakely-scale/agentenv-portsim-plugin/security/advisories/new),
not in a public issue. Include what an attacker could do, how to reproduce it, and the commit you tested.

The env's MCP tools, data plane and extensions have no authentication. Run it on a local machine or a private
network, and don't expose its port publicly.

The env image holds the task packs, and with them every task's reference plan. An agent that can run commands in the
env's container could read them, and one that can reach the extensions could reload its task (which resets the check
and call counters) or submit through `urn:portsim:submit-plan/v1`. Give the agent under test only the MCP tools: no
shell in the env's sandbox and no other route to its port.
