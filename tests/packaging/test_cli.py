"""`agent-env portsim setup` with a stand-in docker: what it builds, and the env it registers."""

from pathlib import Path

import pytest
from agent_env.artifact import DockerImageArtifact
from agent_env.env import Env
from click.testing import CliRunner

from agentenv_portsim import cli
from agentenv_portsim.cli import portsim

ROOT = Path(__file__).resolve().parents[2]


def fake_docker(tmp_path: Path, monkeypatch, build_exit: int = 0) -> Path:
    """A docker on PATH that logs its arguments and reports an arm64 host."""
    log, bin_dir = tmp_path / "docker.log", tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(f'#!/bin/sh\necho "$@" >> {log}\ncase "$1" in\n  version) echo linux/arm64 ;;\n'
                      f"  build) exit {build_exit} ;;\nesac\n")
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin:/bin")
    return log


@pytest.fixture
def stored(monkeypatch):
    """DockerImageArtifact.put without docker save and the registry push: the arguments setup stores the image with."""
    calls = []

    def put(id, *, description, image_name):
        calls.append({"id": id, "image_name": image_name})
        return DockerImageArtifact.put_tar(id, description=description, image_name=f"localhost:5000/{id}:v1",
                                           tar_gz_s3_url="file:///dev/null")

    monkeypatch.setattr(cli.DockerImageArtifact, "put", put)
    return calls


@pytest.mark.parametrize(("args", "platform"), [([], "linux/arm64"), (["--platform", "linux/amd64"], "linux/amd64")])
def test_setup_builds_the_image_and_registers_portsim_on_the_server_provider(local_stores, tmp_path, monkeypatch,
                                                                             stored, args, platform):
    log = fake_docker(tmp_path, monkeypatch)
    result = CliRunner().invoke(portsim, ["setup", "--source", str(ROOT), *args])
    assert result.exit_code == 0, result.output
    assert log.read_text().splitlines()[-1] == f"build --platform {platform} -t agentenv-portsim-env {ROOT}"
    assert stored == [{"id": "mcp-server-portsim", "image_name": "agentenv-portsim-env"}]
    env = Env.get("portsim")
    assert (env.type, env.environment_name, env.env_provider_type) == ("mcp_server", "portsim", "server")
    assert env.docker_image_artifact.image_name == "localhost:5000/mcp-server-portsim:v1"
    assert "Registered env 'portsim' version 1" in result.output


def test_setup_stops_when_the_build_fails(local_stores, tmp_path, monkeypatch, stored):
    fake_docker(tmp_path, monkeypatch, build_exit=1)
    result = CliRunner().invoke(portsim, ["setup", "--source", str(ROOT)])
    assert result.exit_code == 1
    assert "docker build failed" in result.output
    assert stored == []


def test_setup_needs_a_checkout_to_build(tmp_path):
    result = CliRunner().invoke(portsim, ["setup", "--source", str(tmp_path)])
    assert result.exit_code == 2
    assert "is not a checkout of agentenv-portsim-plugin" in result.output
