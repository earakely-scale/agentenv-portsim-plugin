PortSim dock-v1 for training: the 1050 train and 50 eval tasks of PortSimEnv's dock-v1 packs with the PortSim env and its verifier, which `openenv import` and `agent_env.openenv.build_app` serve as they are, with no PortSim setup.

Each task deploys the env in `envs/portsim`, loads one dock-v1 task through `urn:portsim:load-task/v1`, gives one agent upstream's prompts and limits, and grades the plan it submits with `portsim-verifier`. A served task's agent is played from outside, by an OpenEnv client or by TRL through `agent_env.training.trl`; `agent-env run` plays it with portsim-llm, which `agent-env portsim setup --agent` registers.

The splits are `all`, `train`, `eval`, and the train tasks of each tier: `train-busy`, `train-extreme`, `train-standard`, `train-storm`.

```bash
openenv import portsim-dock-v1 --name portsim_dock_v1 --output-dir envs
cd envs/portsim_dock_v1 && MAX_CONCURRENT_ENVS=16 uv run server
```

The env image installs the plugin's v0.5.5 release from GitHub. `agent-env portsim tasks training-pack` writes this folder.

The prompts are derived from PortSimEnv's dock-v1 task packs (CC BY-SA 4.0). Contains data from the Port de Barcelona open data portal.
