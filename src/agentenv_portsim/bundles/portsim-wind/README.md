PortSim wind: one week at a Port of Barcelona quay played in watches on the gateway's virtual clock, with the port's pilots and tugs, in a real weather week at the Dique Sur anemometer: Barcelona Port Control sends the wind forecast published by each watch, and the week is graded on the wind that blew.

Every task deploys the env registered as `portsim-wind` on the gateway provider (run `agent-env portsim setup` once)
and loads one week of the dock-v1-wind pack through the env's `urn:portsim:live-load/v1` extension. Each week is a
dock-v1-marine week moved into a weather week: above 25 kn ships of 300 m or more may not berth or leave and each
movement takes one more tug, and above 30 kn no ship moves, in the hours the wind observed at the anemometer passed
those limits. At every watch the situation holds the latest forecast published by then and the wind observed so far,
nothing later. The task hides the env's `port_notice` tool from the agent's role, registers one trigger per watch that
delivers the watch's notices, its forecast last, through `port_notice` when the agent's `advance` reaches it, and arms
the clock frozen at the week's start. After the play, `urn:portsim:end-week/v1` runs any watches the agent didn't reach
and grades the week. The `portsim-live-verifier` artifact reads the week from the env's `data/get` and scores the run
with the reward of the executed week; a week that never finished, or whose notices broke the reveal schedule, fails the
step, so the run is not scored.

- `week` plays `dock-24B-w06x1-busy-0-e15` with the portsim-llm agent (`agent-env portsim setup --agent`), six watches.
- `wiring-noplay` runs the same steps without the agent and needs no model: end-week delivers every watch's notices
  itself, the week ends with no window confirmed, and it scores 0 with the audit passing.

The task pack and the prompts and notices in these tasks are CC BY-SA 4.0, except the weather they show (the forecast
notices and the wind windows), which keeps its sources' terms (NOTICE, data/LICENSE). The other traffic is derived from
the Port of Barcelona's 2024 calls of every ship type (CC BY-SA 4.0). Contains data from the Port de Barcelona open data
portal. Contains modified ECMWF open data (CC BY 4.0, © ECMWF) and wind windows derived from the Servei Meteorològic de
Catalunya's (Meteocat) XEMA station Y7.
