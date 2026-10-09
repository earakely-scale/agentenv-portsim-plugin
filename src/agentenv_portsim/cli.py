"""`agent-env portsim`: build and register the PortSim env and the portsim-llm agent, write the eval tasks, sweep
models over them, and watch the recorded runs."""

import json
import subprocess
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

import click
from agent_env.a2a_agent import A2AAgent
from agent_env.artifact import DockerImageArtifact
from agent_env.env import MCPServerEnv

from .record import record_command
from .schedule import LIVE_ENV, MARINE_ENV, WIND_ENV
from .sweep import sweep_group
from .tasks import tasks_group
from .view import view_command

ENV_ID = "portsim"
IMAGE = "agentenv-portsim-env"
AGENT_ID = "portsim-llm"
AGENT_IMAGE = "agentenv-portsim-agent"
AGENT_MODEL = "anthropic/claude-sonnet-5-5"
REPO = "https://github.com/earakely-scale/agentenv-portsim-plugin"


@click.group()
def portsim():
    """PortSim: build and register the env and agent, write the eval tasks, sweep models over them, and watch the
    recorded runs."""


def _installed_commit() -> str | None:
    """The git commit a `pip install git+...` or uv git source installed this package from (PEP 610), if it did."""
    try:
        direct = json.loads(distribution("agentenv-portsim").read_text("direct_url.json") or "{}")
    except PackageNotFoundError:
        return None
    return direct.get("vcs_info", {}).get("commit_id")


def _checkout(source: Path | None) -> str:
    """What to build from: ``source``, else the checkout an editable install runs from, else the cwd, else the commit
    of this repo a git install came from, which Docker fetches itself as a git build context."""
    for root in [source] if source else [Path(__file__).resolve().parents[2], Path.cwd()]:
        if (root / "Dockerfile").is_file() and (root / "src/agentenv_portsim").is_dir():
            return str(root)
    if source:
        raise click.UsageError(f"{source} is not a checkout of agentenv-portsim-plugin (no Dockerfile and src/)")
    if commit := _installed_commit():
        return f"{REPO}.git#{commit}"
    raise click.UsageError(f"no checkout of agentenv-portsim-plugin found; clone {REPO} and pass --source")


def _context(root: str, subdir: str) -> str:
    return f"{root}:{subdir}" if "#" in root else str(Path(root) / subdir)


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


def _register_agent(root: str, build_platform: str) -> None:
    click.echo(f"Building {AGENT_IMAGE} for {build_platform}")
    build = ["docker", "build", "--platform", build_platform, "-t", AGENT_IMAGE, _context(root, f"agents/{AGENT_ID}")]
    if subprocess.run(build).returncode:
        raise click.ClickException("docker build of the portsim-llm agent failed")
    artifact = DockerImageArtifact.put(id=AGENT_IMAGE, image_name=AGENT_IMAGE,
                                       description="portsim-llm: PortSimEnv's harness loop as an A2A agent")
    agent = A2AAgent.put(id=AGENT_ID, docker_image_artifact=artifact, metadata={"default_model": AGENT_MODEL})
    click.echo(f"Registered A2A agent {agent.id!r} version {agent.version} (image {artifact.image_name})")


@portsim.command()
@click.option("--platform", "build_platform",
              help="Platform to build for. Default: the Docker host's (linux/arm64 on Apple Silicon); "
                   "remote sandboxes need linux/amd64.")
@click.option("--source", type=click.Path(exists=True, file_okay=False, path_type=Path),
              help="Checkout of this repo to build. Default: the one an editable install runs from, the cwd, or the "
                   "GitHub commit a git install came from.")
@click.option("--agent", is_flag=True, help="Also build the portsim-llm agent for the same platform and register it.")
def setup(build_platform: str | None, source: Path | None, agent: bool):
    """Build the env image and register it as the MCP server env `portsim` on the `server` provider and as
    `portsim-live`, `portsim-marine` and `portsim-wind` on the `gateway` provider; with --agent, the portsim-llm agent
    too."""
    root = _checkout(source)
    build_platform = build_platform or _docker_platform()
    click.echo(f"Building {IMAGE} for {build_platform} from {root}")
    if subprocess.run(["docker", "build", "--platform", build_platform, "-t", IMAGE, root]).returncode:
        raise click.ClickException("docker build failed")
    click.echo("Storing the image (docker save, can take a minute)")
    artifact = DockerImageArtifact.put(id=IMAGE, image_name=IMAGE,
                                       description="PortSim env: the berth-planning MCP server and the dock-v1 packs")
    env = MCPServerEnv.put(id=ENV_ID, docker_image_artifact=artifact, environment_name=ENV_ID,
                           env_provider_type="server")
    click.echo(f"Registered env {env.id!r} version {env.version} (image {artifact.image_name})")
    wind = MCPServerEnv.put(id=WIND_ENV, docker_image_artifact=artifact, environment_name=WIND_ENV,
                            env_provider_type="gateway")
    click.echo(f"Registered env {wind.id!r} version {wind.version} (image {artifact.image_name})")
    live = MCPServerEnv.put(id=LIVE_ENV, docker_image_artifact=artifact, environment_name=LIVE_ENV,
                            env_provider_type="gateway")
    click.echo(f"Registered env {live.id!r} version {live.version} (image {artifact.image_name})")
    marine = MCPServerEnv.put(id=MARINE_ENV, docker_image_artifact=artifact, environment_name=MARINE_ENV,
                              env_provider_type="gateway")
    click.echo(f"Registered env {marine.id!r} version {marine.version} (image {artifact.image_name})")
    if agent:
        _register_agent(root, build_platform)
    click.echo("Next: agent-env run portsim --task smoke")


portsim.add_command(tasks_group)
portsim.add_command(sweep_group)
portsim.add_command(view_command)
portsim.add_command(record_command)
