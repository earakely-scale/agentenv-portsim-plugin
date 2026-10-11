PortSim lines: a wind week at a Port of Barcelona quay where the shipping lines answer back. Each ship's agent, the firm that deals with the port for its line, is its own A2A agent the planner can message: it reports the ship's ETA as the ship nears, answers when asked, and agrees an arrival time when the ship can make it by slowing down. Ships berth first come, first served, and an hour at anchor costs what an hour late does.

Every task deploys the env registered as `portsim-lines` on the gateway provider (run `agent-env portsim setup` once)
and loads one week of the dock-v1-lines pack through the env's `urn:portsim:live-load/v1` extension. Each week is a
dock-v1-wind week with each ship's agent (named in the port's 2024 record), its previous port's distance and how far off
its agent's ETAs run: most ships arrive later than their agent says, by less as they near. The planner sees the ETAs
as they come; the week is graded on when the ships really arrived. A ship slowed at the planner's request arrives at
the agreed hour and keeps its turn in the queue.

The task hides `port_notice` and the agents' two tools (`ship_status`, `agree_arrival`) from the planner's role and
gives the `line` role those two tools only. It registers one trigger per watch that delivers the watch's notices,
the agents' ETA reports and arrival calls among them, through `port_notice` when the planner's `advance` reaches it,
and arms the clock frozen at the week's start. It deploys the portsim-llm agent as the planner, then one portsim-line
agent per firm with ships in the week, named by the firm's id, under the `line` role, and peers the planner with them,
so its model gets a `message_agent` tool. After the play, `urn:portsim:end-week/v1` runs any watches the planner didn't
reach and grades the week. The `portsim-live-verifier` artifact reads the week from the env's `data/get` and scores the
run with the reward of the executed week; a week that never finished, or whose notices broke the reveal schedule, fails
the step, so the run is not scored.

- `week` plays `dock-24B-w06x1-busy-0-e15` with the portsim-llm agent and eight ships' agents
  (`agent-env portsim setup --agent`), six watches.
- `wiring-noplay` runs the same steps without any agent and needs no model: end-week delivers every watch's notices
  itself, the week ends with no window confirmed, and it scores 0 with the audit passing.

The task pack and the prompts and notices in these tasks are CC BY-SA 4.0, except the weather they show (the forecast
notices and the wind windows), which keeps its sources' terms (NOTICE, data/LICENSE). The ships' agents and the other
traffic are derived from the Port de Barcelona's 2024 calls (CC BY-SA 4.0); the distances from NGA Pub. 151 (no
copyright claimed).
