"""The viewer's 3D twin of the Port of Barcelona: OpenStreetMap-derived (ODbL 1.0) data, so never shipped here, but
downloaded once from PortSimEnv's public bucket into the user cache and checked against b0f4c2f's files."""

import hashlib
import os
import urllib.request
from pathlib import Path

import click

BUCKET = "https://huggingface.co/buckets/FineEnvs/PortSimEnv/resolve/twin/"
ATTRIBUTION = "Port of Barcelona twin © OpenStreetMap contributors (ODbL) · terrain: Terrain Tiles (AWS)"
COMMIT = "b0f4c2f"
FILES = {
    "twin.json.gz": (571_172, "d260a98311ce9dda0cf52dab50bb05af2e0c3c0c243d951c76cb5150d160ec3f"),
    "terrain.png": (121_683, "eef90cfb00888712bc1ee3a9c1bd4a6c08c0f14ba338f16d8252fc1e7044fcf4"),
    "cover.png": (33_246, "281bd42036a91a8d5848f0dc52272e537b3e44bd7289393ee5fc3a6e4af8839f"),
    "scenery.json.gz": (1_752_619, "09292d69e0a10f7b9f328ae831ad87cfdf38e64f593564188738a3804049c154"),
    "surface.webp": (1_706_666, "0248951c1b8dadcefb28c2113fe54a34b3b4099fa32e7528e654ffe7de0da001"),
}


def cache_dir() -> Path:
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "agentenv-portsim" / "twin" / COMMIT


def _valid(path: Path, size: int, sha256: str) -> bool:
    return path.is_file() and path.stat().st_size == size and hashlib.sha256(path.read_bytes()).hexdigest() == sha256


def ensure(echo=click.echo) -> Path:
    """The cache directory, holding the five files."""
    root = cache_dir()
    missing = [name for name, pin in FILES.items() if not _valid(root / name, *pin)]
    if missing:
        echo(f"Downloading the 3D twin into {root}. {ATTRIBUTION}")
        root.mkdir(parents=True, exist_ok=True)
    for name in missing:
        with urllib.request.urlopen(BUCKET + name, timeout=120) as response:
            body = response.read()
        if hashlib.sha256(body).hexdigest() != FILES[name][1]:
            raise click.ClickException(f"{BUCKET}{name} is not the file pinned at {COMMIT} (sha256 mismatch)")
        part = root / f"{name}.part"
        part.write_bytes(body)
        part.replace(root / name)
    return root
