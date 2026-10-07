"""The wheel carries berth_core, the plugin and its bundle, and the task packs as package data, where the server finds
them without BERTH_TASKS_DIR, installed from the wheel or editable."""

import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROBE = ("from pathlib import Path; import agentenv_portsim, berth_core; "
         "from agentenv_portsim.server import PortSimEnv; pack = PortSimEnv().pack; "
         "print(Path(agentenv_portsim.__file__).parent, Path(berth_core.__file__).parent, pack.root, len(pack.tasks))")


@pytest.fixture(scope="module")
def wheel(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    subprocess.run([sys.executable, "-m", "hatchling", "build", "-t", "wheel", "-d", str(out)], cwd=ROOT, check=True,
                   capture_output=True)
    return next(out.glob("agentenv_portsim-*.whl"))


def sources(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def test_the_wheel_carries_berth_core_the_plugin_and_the_data_unchanged(wheel):
    with zipfile.ZipFile(wheel) as whl:
        packed = {name: whl.read(name) for name in whl.namelist()}
    expected = ({f"berth_core/{k}": v for k, v in sources(ROOT / "src/berth_core").items()}
                | {f"agentenv_portsim/{k}": v for k, v in sources(ROOT / "src/agentenv_portsim").items()}
                | {f"agentenv_portsim/data/{k}": v for k, v in sources(ROOT / "data").items()})
    assert {k: v for k, v in packed.items() if k in expected} == expected
    assert {name.split("/", 1)[0] for name in packed} == {
        "berth_core", "agentenv_portsim", wheel.name.removesuffix("-py3-none-any.whl") + ".dist-info"}
    licenses = {name.split(".dist-info/licenses/", 1)[1] for name in packed if ".dist-info/licenses/" in name}
    assert licenses == {"LICENSE", "NOTICE", "data/LICENSE"}


def served(path: Path) -> list[str]:
    """The server's package, berth_core, first pack and task count, with ``path`` first on sys.path."""
    env = {k: v for k, v in os.environ.items() if k != "BERTH_TASKS_DIR"} | {"PYTHONPATH": str(path)}
    return subprocess.run([sys.executable, "-c", PROBE], env=env, cwd=path, check=True, capture_output=True,
                          text=True).stdout.split()


def test_a_wheel_install_serves_the_packs_from_its_package_data(wheel, tmp_path):
    with zipfile.ZipFile(wheel) as whl:
        whl.extractall(tmp_path)
    assert served(tmp_path) == [str(tmp_path / "agentenv_portsim"), str(tmp_path / "berth_core"),
                                str(tmp_path / "agentenv_portsim/data/dock-v1-eval"), "1100"]


def test_an_editable_install_serves_the_packs_through_the_data_link():
    """An editable install puts src/ on sys.path; src/agentenv_portsim/data links to data/."""
    src = ROOT / "src"
    assert served(src) == [str(src / "agentenv_portsim"), str(src / "berth_core"),
                           str(src / "agentenv_portsim/data/dock-v1-eval"), "1100"]
