# Contributing

Thanks for helping. Fixes, tasks, tests, docs and bug reports are all welcome.

## How a change gets in

1. **Talk first about anything large.** Open an issue for a new task, extension or change to how the env runs
   before you write it, so we agree on the shape. Small fixes can go straight to a pull request.
2. **Fork, branch and open a pull request against `main`.** Fill in the template: what changes, why, and how you
   tested it.
3. **CI must pass:** lint, the tests on Python 3.11 and 3.12, `agent-env plugin check`, and the image build that
   runs the three wiring tasks and the golden and replay tests against the image.
4. **The maintainer reviews and approves every pull request.** `main` is protected: a pull request merges only
   with an approving review from the code owner ([.github/CODEOWNERS](.github/CODEOWNERS)), green checks and its
   conversations resolved. Pull requests are squash-merged, so the title becomes the commit message.

First-time contributors' CI runs wait for the maintainer's approval, as GitHub does for public repositories.

## Setup

You need git, [uv](https://docs.astral.sh/uv/) and, for the image, Docker with buildx.

```bash
git clone https://github.com/<you>/agentenv-portsim-plugin && cd agentenv-portsim-plugin
uv venv && uv pip install -e '.[dev]'
.venv/bin/pytest && .venv/bin/ruff check .
```

To try a change end to end, install the checkout into the `agent-env` tool and run the wiring tasks:

```bash
uv tool install agentenv-framework --with-editable .
agent-env portsim setup
agent-env run portsim --task smoke --task wiring-infeasible --task wiring-nosubmit
```

## Where things go

| Change | Code | Tests and docs |
|---|---|---|
| The env: its tools, extensions or data plane | `src/agentenv_portsim/server.py` | `tests/env/`; the README's tool table |
| A task | `src/agentenv_portsim/bundles/portsim/tasks/` | `tests/packaging/`; the bundle's README and the README's task table |
| The verifier | `src/agentenv_portsim/bundles/portsim/artifacts/portsim-verifier/verify.py` | `tests/packaging/` |
| `agent-env portsim setup` | `src/agentenv_portsim/cli.py` | `tests/packaging/` |
| The env image | `Dockerfile` | the CI `image` job |
| PortSimEnv's core or task packs | never here: `src/berth_core/` and `data/` are copied unchanged from upstream ([VENDORED.md](VENDORED.md)) | a new upstream commit is vendored whole, and VENDORED.md names it |

## Conventions

- **Parity comes first.** The tools' names, descriptions, input schemas, output and error text and limits match
  PortSimEnv's exactly, and the replay and golden tests hold them to it, so a change to what an agent sees isn't
  taken here.
- **Vendored files stay unchanged.** `src/berth_core/` and `data/` match upstream byte for byte; the task packs'
  sha256 is checked when they load.
- **The answer key stays in the image.** No tool, extension, route or `data/get` field returns a task's reference
  plans; `data/get`'s grade, there only after a submit, includes the optimal and naive costs.
- **Code:** match the code around it. `ruff check .` must pass. Name things so the code reads without comments;
  write a short docstring only for why something is the way it is.
- **Tests:** a fix comes with a test that fails without it. Tests set `BERTH_TASKS_DIR` themselves; they call no
  model.
- **No secrets or private endpoints** in code, tests, docs or task files: model keys come from agent-env's secret
  store, and examples use placeholders such as `https://your-litellm-proxy`.
- **Licensing:** code contributions are licensed under the Apache License 2.0, like the rest of the code. Anything
  derived from the task packs (plans, situations, recorded outputs) is CC BY-SA 4.0 and must be listed in
  [NOTICE](NOTICE). Recorded episodes from the published dataset are fetched by the tests, never committed.

## Reporting bugs and security issues

Open an issue with the task or command, the PortSim task id, what you expected, what happened, and the run's instance
id or log. For a security issue, use GitHub's private vulnerability reporting instead ([SECURITY.md](SECURITY.md)).
