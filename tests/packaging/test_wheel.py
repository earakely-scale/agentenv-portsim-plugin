"""The wheel carries the plugin and its bundle, and the task packs as package data, where the server finds them without
BERTH_TASKS_DIR, installed from the wheel or editable; berth_core comes from FineEnvs at the commit the wheel and the
image both pin."""

import configparser
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROBE = ("from pathlib import Path; import agentenv_portsim; "
         "from agentenv_portsim.server import PortSimEnv; pack = PortSimEnv().pack; "
         "print(Path(agentenv_portsim.__file__).parent, pack.root, len(pack.tasks))")
UPSTREAM = "b0f4c2f9526e3c45d608b4f92f6ec6c71fecc152"


@pytest.fixture(scope="module")
def wheel(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    subprocess.run([sys.executable, "-m", "hatchling", "build", "-t", "wheel", "-d", str(out)], cwd=ROOT, check=True,
                   capture_output=True)
    return next(out.glob("agentenv_portsim-*.whl"))


def sources(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def test_the_wheel_carries_the_plugin_and_the_data_unchanged(wheel):
    with zipfile.ZipFile(wheel) as whl:
        packed = {name: whl.read(name) for name in whl.namelist()}
    expected = ({f"agentenv_portsim/{k}": v for k, v in sources(ROOT / "src/agentenv_portsim").items()}
                | {f"agentenv_portsim/data/{k}": v for k, v in sources(ROOT / "data").items()})
    assert {k: v for k, v in packed.items() if k in expected} == expected
    assert {name.split("/", 1)[0] for name in packed} == {
        "agentenv_portsim", wheel.name.removesuffix("-py3-none-any.whl") + ".dist-info"}
    licenses = {name.split(".dist-info/licenses/", 1)[1] for name in packed if ".dist-info/licenses/" in name}
    assert licenses == {"LICENSE", "NOTICE", "data/LICENSE"}


def test_the_wheel_declares_each_bundle_it_carries(wheel):
    with zipfile.ZipFile(wheel) as whl:
        names = whl.namelist()
        entry_points = configparser.ConfigParser()
        entry_points.read_string(whl.read(next(n for n in names if n.endswith(".dist-info/entry_points.txt"))).decode())
    bundles = ["portsim", "portsim-live", "portsim-marine", "portsim-wind"]
    assert dict(entry_points["agent_env.bundles"]) == dict.fromkeys(bundles, "agentenv_portsim.bundles")
    assert sorted({n.split("/")[2] for n in names if n.startswith("agentenv_portsim/bundles/") and n.count("/") > 2}
                  ) == bundles


def test_the_wheel_and_the_image_pin_berth_core_to_the_same_fineenvs_commit(wheel):
    with zipfile.ZipFile(wheel) as whl:
        metadata = whl.read(next(n for n in whl.namelist() if n.endswith(".dist-info/METADATA"))).decode()
    [pin] = [line.removeprefix("Requires-Dist: ") for line in metadata.splitlines()
             if line.startswith("Requires-Dist: berth-core")]
    assert f"/archive/{UPSTREAM}.tar.gz#" in pin
    assert f'"{pin}"' in (ROOT / "Dockerfile").read_text()


def served(path: Path) -> list[str]:
    """The server's package, first pack and task count, with ``path`` first on sys.path."""
    env = {k: v for k, v in os.environ.items() if k != "BERTH_TASKS_DIR"} | {"PYTHONPATH": str(path)}
    return subprocess.run([sys.executable, "-c", PROBE], env=env, cwd=path, check=True, capture_output=True,
                          text=True).stdout.split()


def test_a_wheel_install_serves_the_packs_from_its_package_data(wheel, tmp_path):
    with zipfile.ZipFile(wheel) as whl:
        whl.extractall(tmp_path)
    assert served(tmp_path) == [str(tmp_path / "agentenv_portsim"),
                                str(tmp_path / "agentenv_portsim/data/dock-v1-eval"), "1100"]


def test_an_editable_install_serves_the_packs_through_the_data_link():
    """An editable install puts src/ on sys.path; src/agentenv_portsim/data links to data/."""
    src = ROOT / "src"
    assert served(src) == [str(src / "agentenv_portsim"), str(src / "agentenv_portsim/data/dock-v1-eval"), "1100"]
