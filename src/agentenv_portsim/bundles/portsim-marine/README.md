PortSim marine: one week at a Port of Barcelona quay played in watches on the gateway's virtual clock, with the port's pilots and tugs shared with its other 2024 traffic, the news arriving from the ships, the harbour master, terminal ops, the tug company and the pilot station, graded against the hindsight optimum.

Every task deploys the env registered as `portsim-marine` on the gateway provider (run `agent-env portsim setup` once)
and loads one week of the dock-v1-marine pack through the env's `urn:portsim:live-load/v1` extension. Each berthing and
departure takes a pilot and tugs in its hour from the port's pools, shared with the other traffic; an hour short of
either is a rule break for each of our ships moving in it, and the situation lists the pilots and tugs free each hour.
The task hides the env's `port_notice` tool from the agent's role, registers one trigger per watch that delivers the
watch's notices through `port_notice` when the agent's `advance` reaches it, and arms the clock frozen at the week's
start. After the play, `urn:portsim:end-week/v1` runs any watches the agent didn't reach and grades the week. The
`portsim-live-verifier` artifact reads the week from the env's `data/get` and scores the run with the reward of the
executed week; a week that never finished, or whose notices broke the reveal schedule, fails the step, so the run is
not scored.

- `week` plays `dock-24B-w07x1-busy-0` with the portsim-llm agent (`agent-env portsim setup --agent`), seven watches.
- `wiring-noplay` runs the same steps without the agent and needs no model: end-week delivers every watch's notices
  itself, the week ends with no window confirmed, and it scores 0 with the audit passing.

The task pack and the prompts and notices in these tasks are CC BY-SA 4.0. The other traffic is derived from the Port of
Barcelona's 2024 calls of every ship type (CC BY-SA 4.0). Contains data from the Port de Barcelona open data portal.
