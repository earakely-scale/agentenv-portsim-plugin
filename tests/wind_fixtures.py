"""The wind fixtures: data/'s wind files built from synthetic weather (tests/wind/synthetic.py) by
scripts/wind_references.py, for the tests to use in place of the real pack."""

from pathlib import Path

from agentenv_portsim import wind

DATA = Path(__file__).resolve().parents[1] / "data"
FIXTURES = Path(__file__).resolve().parent / "wind" / "fixtures"
PACK_DIR = FIXTURES / "dock-v1-wind"
WEATHER = FIXTURES / "wind" / "weather.jsonl"
REFERENCES = FIXTURES / "wind" / "references.jsonl"
STORM_TASK = "dock-24B-w07x1-busy-0-e00"
BUST_TASK = "dock-24B-w07x1-busy-0-e01"
OTHER_TASK = "dock-36A-w37x1-standard-0-e00"


def use(monkeypatch) -> None:
    monkeypatch.setattr(wind, "pack_dir", lambda: PACK_DIR)
    monkeypatch.setattr(wind, "REFERENCES", REFERENCES)


def tasks_dir(tmp_path: Path) -> str:
    """A BERTH_TASKS_DIR for a server subprocess: dock-v1-eval, with the fixture pack beside it."""
    root = tmp_path / "packs"
    root.mkdir()
    (root / "dock-v1-eval").symlink_to(DATA / "dock-v1-eval")
    (root / "dock-v1-wind").symlink_to(PACK_DIR)
    return str(root / "dock-v1-eval")
