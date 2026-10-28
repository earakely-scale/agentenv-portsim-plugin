"""`agent-env portsim tasks training-pack` and the pack committed under packs/: the pack is what it writes for the
release its env pins, its env installs the server the repo's Dockerfile builds, its splits are the dock-v1 packs and
the train tiers, and every task passes the checks `agent-env run` makes before a store and runs as an episode with one
agent played from outside."""

import json
import re
import tomllib
from collections import Counter
from pathlib import Path

from agent_env.bundle.parse import BundleKind, parse_bundle
from agent_env.bundle.plan import check_bundle
from agent_env.bundle.resolve import resolve_bundle
from agent_env.task import EpisodeSpec, Task
from click.testing import CliRunner

from agentenv_portsim import tasks
from agentenv_portsim.cli import portsim

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "packs" / tasks.TRAINING_PACK
SOURCE = "https://github.com/earakely-scale/agentenv-portsim-plugin"


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def release(pack: Path) -> str:
    return re.search(r"/archive/refs/tags/v([^/]+)\.tar\.gz", (pack / "envs/portsim/Dockerfile").read_text())[1]


def statement(dockerfile: Path, instruction: str) -> str:
    """The first ``instruction`` of ``dockerfile``, with its continuation lines joined."""
    lines = re.sub(r"\s*\\\n\s*", " ", dockerfile.read_text()).splitlines()
    return next(line for line in lines if line.startswith(instruction))


def test_the_committed_pack_is_what_training_pack_writes_for_the_release_its_env_pins(tmp_path):
    names = tasks.training_pack(tmp_path / "pack", release(PACK))

    assert snapshot(tmp_path / "pack") == snapshot(PACK), "rewrite it with: agent-env portsim tasks training-pack"
    assert len(names) == 1100


def test_its_env_installs_the_server_the_repos_dockerfile_builds_from_that_release():
    env, repo = PACK / "envs/portsim/Dockerfile", ROOT / "Dockerfile"
    requirements = re.findall(r'"([^"]+)"', statement(repo, "RUN pip install"))

    assert re.findall(r'"([^"]+)"', statement(env, "RUN pip install")) == [
        *requirements, f"agentenv-portsim @ {SOURCE}/archive/refs/tags/v{release(PACK)}.tar.gz"]
    for instruction in ("FROM ", "LABEL ", "RUN useradd ", "USER ", "EXPOSE ", "CMD "):
        assert statement(env, instruction) == statement(repo, instruction)
    assert statement(repo, "ENV ").startswith(statement(env, "ENV ") + " BERTH_TASKS_DIR=")
    assert tomllib.loads((PACK / "envs/portsim/env.toml").read_text()) == {
        "environment_name": "portsim", "env_provider_type": "server"}


def test_the_splits_are_the_dock_v1_packs_and_the_train_tiers():
    evals = {path.stem: tomllib.loads(path.read_text())["tasks"] for path in (PACK / "evals").glob("*.toml")}
    train = [t.task_id for t in tasks.pack_tasks("dock-v1-train")]

    assert (evals["train"], evals["eval"]) == (train, [t.task_id for t in tasks.pack_tasks("dock-v1-eval")])
    assert {name: len(ids) for name, ids in evals.items()} == {
        "train": 1050, "eval": 50, "train-busy": 260, "train-extreme": 262, "train-standard": 266, "train-storm": 262}
    assert sorted(id for tier in tasks.TIERS for id in evals[f"train-{tier}"]) == sorted(train)


def test_every_task_passes_the_checks_run_makes_and_is_an_episode_with_one_agent_played_from_outside(local_stores):
    parsed = parse_bundle(PACK)
    check_bundle(resolve_bundle(parsed))

    assert Counter(entry.kind for entry in parsed.entries) == {
        BundleKind.TASK: 1100, BundleKind.EVAL: 6, BundleKind.ENV: 1, BundleKind.ARTIFACT: 1}
    assert parsed.description.startswith("PortSim dock-v1 for training: the 1050 train and 50 eval tasks")
    for path in (PACK / "tasks").glob("*.json"):
        spec = EpisodeSpec.from_task(Task.from_dict({"id": path.stem, "steps": json.loads(path.read_text())}))
        assert spec.trainer_agents == ("default-agent",)


def test_training_pack_writes_into_packs_by_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(portsim, ["tasks", "training-pack"])

    assert result.exit_code == 0, result.output
    assert result.output == ("Wrote 1100 tasks into packs/portsim-dock-v1; serve it with: openenv import "
                             "packs/portsim-dock-v1 --name portsim_dock_v1\n")
    assert len(list((tmp_path / "packs/portsim-dock-v1/tasks").iterdir())) == 1100
