"""The wheel carries berth_core, the plugin and its bundle, and the task packs where the installed plugin finds them."""

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKS = ["dock-v1-eval", "dock-v1-train"]


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


def test_the_installed_wheel_loads_the_task_packs_from_its_package_data(wheel, tmp_path):
    with zipfile.ZipFile(wheel) as whl:
        whl.extractall(tmp_path)
    probe = ("from importlib.resources import files; import berth_core; "
             f"data = files('agentenv_portsim') / 'data'; pack = berth_core.TaskPack([data / p for p in {PACKS!r}]); "
             "print(berth_core.__file__, len(pack.tasks), *pack.splits())")
    out = subprocess.run([sys.executable, "-c", probe], env={"PYTHONPATH": str(tmp_path)}, cwd=tmp_path, check=True,
                         capture_output=True, text=True).stdout.split()
    assert Path(out[0]).is_relative_to(tmp_path)
    assert out[1:] == ["1100", "eval", "train"]
