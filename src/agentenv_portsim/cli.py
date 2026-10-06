"""`agent-env portsim`: build the PortSim env image and register it."""

import subprocess
from pathlib import Path

import click
from agent_env.artifact import DockerImageArtifact
from agent_env.env import MCPServerEnv

from .sweep import sweep_group
from .tasks import tasks_group

ENV_ID = "portsim"
IMAGE = "agentenv-portsim-env"
REPO = "https://github.com/earakely-scale/agentenv-portsim-plugin"


@click.group()
def portsim():
    """PortSim: build and register the env."""


def _checkout(source: Path | None) -> Path:
    """The checkout of this repo to build from: ``source``, else the one an editable install runs from, else the cwd."""
    for root in [source] if source else [Path(__file__).resolve().parents[2], Path.cwd()]:
        if (root / "Dockerfile").is_file() and (root / "src/berth_core").is_dir():
            return root
    if source:
        raise click.UsageError(f"{source} is not a checkout of agentenv-portsim-plugin (no Dockerfile and berth_core)")
    raise click.UsageError(f"no checkout of agentenv-portsim-plugin found; clone {REPO} and pass --source")


def _docker_platform() -> str:
    """The Docker host's own platform: the local `server` provider pulls images without emulation."""
    try:
        out = subprocess.run(["docker", "version", "--format", "{{.Server.Os}}/{{.Server.Arch}}"], capture_output=True,
                             text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise click.ClickException(f"docker is not available: {e}") from e
    if out.returncode:
        raise click.ClickException(f"docker is not running: {out.stderr.strip()}")
    return out.stdout.strip()


@portsim.command()
@click.option("--platform", "build_platform",
              help="Platform to build for. Default: the Docker host's (linux/arm64 on Apple Silicon); "
                   "remote sandboxes need linux/amd64.")
@click.option("--source", type=click.Path(exists=True, file_okay=False, path_type=Path),
              help="Checkout of this repo to build. Default: the one an editable install runs from, or the cwd.")
def setup(build_platform: str | None, source: Path | None):
    """Build the env image and register it as the MCP server env `portsim` on the `server` provider."""
    root = _checkout(source)
    build_platform = build_platform or _docker_platform()
    click.echo(f"Building {IMAGE} for {build_platform} from {root}")
    if subprocess.run(["docker", "build", "--platform", build_platform, "-t", IMAGE, str(root)]).returncode:
        raise click.ClickException("docker build failed")
    click.echo("Storing the image (docker save, can take a minute)")
    artifact = DockerImageArtifact.put(id=IMAGE, image_name=IMAGE,
                                       description="PortSim env: the berth-planning MCP server and the dock-v1 packs")
    env = MCPServerEnv.put(id=ENV_ID, docker_image_artifact=artifact, environment_name=ENV_ID,
                           env_provider_type="server")
    click.echo(f"Registered env {env.id!r} version {env.version} (image {artifact.image_name})")
    click.echo("Next: agent-env run portsim --task smoke")


portsim.add_command(tasks_group)
portsim.add_command(sweep_group)
