PortSim: re-plan a disrupted week of container-ship berthing at a Port of Barcelona quay through MCP tools, graded against the CP-SAT optimum.

Every task deploys the env registered as `portsim` (run `agent-env portsim setup` once) and loads one task of the
dock-v1 packs through the env's `urn:portsim:load-task/v1` extension. The `portsim-verifier` artifact reads the
episode from the env's `data/get` and scores the run with the reward the env gave the submitted plan; a run that
submitted nothing scores 0, and an env that can't report fails the step.

The wiring tasks need no model and no agent. Each loads `dock-24B-w07x1-busy-0`, and the first two submit a fixed plan
through `urn:portsim:submit-plan/v1`, which grades it as the `submit_plan` tool does:

- `smoke` submits the task's stored optimal plan and scores 1.0, so `agent-env run portsim --task smoke` prints
  `passed`.
- `wiring-infeasible` submits that plan with ship 1 berthed on top of ship 0, which breaks the rules; it scores at most
  0.2.
- `wiring-nosubmit` submits nothing and scores 0.

The task packs and the plans in these tasks are CC BY-SA 4.0. Contains data from the Port de Barcelona open data
portal.
