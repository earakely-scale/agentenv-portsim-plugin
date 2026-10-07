# Vendored from FineEnvs

| Here | Upstream |
|---|---|
| `data/dock-v1-eval/` | `07-simulation-environments/portsim-v1/envs/berth_planning/tasks/dock-v1-eval/` (`manifest.json`, `tasks.jsonl`) |
| `data/dock-v1-train/` | `07-simulation-environments/portsim-v1/envs/berth_planning/tasks/dock-v1-train/` (`manifest.json`, `tasks.jsonl.gz`) |
| `data/published/dock-eval50/index.json` | `07-simulation-environments/portsim-v1/results/rollouts/dock-eval50/index.json` |
| `src/agentenv_portsim/web/upstream/` | `07-simulation-environments/portsim-v1/envs/berth_planning/openenv/berth_openenv/web/`: the viewer's 23 files and `twin/SOURCES.md`; not `fixtures/`, `dev_server.py`, `img/` or the five twin data files |

Source: [adithya-s-k/FineEnvs](https://github.com/adithya-s-k/FineEnvs) at commit `b0f4c2f`, copied unchanged.

`berth_core` isn't copied: the package depends on FineEnvs' `berth-core`
(`07-simulation-environments/portsim-v1/envs/berth_planning/core/`) at the same commit, pinned in `pyproject.toml` and
the `Dockerfile`, and `tests/packaging/test_wheel.py` checks that both pin it.

- `berth_core` and the viewer are Apache-2.0, by Adithya S Kolavi. `tests/viewer/test_vendored.py` pins the viewer's
  files.
- The task packs are built from Port of Barcelona open data and are CC BY-SA 4.0 (`data/LICENSE`). Contains data from the Port de Barcelona open data portal.
- The viewer's 3D twin of the Port of Barcelona (`twin.json.gz`, `terrain.png`, `cover.png`, `scenery.json.gz`,
  `surface.webp`) is © OpenStreetMap contributors (ODbL 1.0), with terrain from Terrain Tiles on AWS
  (`twin/SOURCES.md`), and is not stored here: `agent-env portsim view` and `record` download it from PortSimEnv's
  public bucket ([FineEnvs/PortSimEnv](https://huggingface.co/buckets/FineEnvs/PortSimEnv), `twin/`) into
  `~/.cache/agentenv-portsim/twin/b0f4c2f/` and check each file against b0f4c2f's (`src/agentenv_portsim/twin.py`).
