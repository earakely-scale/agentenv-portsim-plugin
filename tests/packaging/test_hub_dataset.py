"""scripts/hub_dataset.py's rows, its typed transcripts and the card it writes for agent-env hf run, and the Hub
sources in hub/ pinned to this version."""

import importlib.util
import io
import json
import tomllib
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from huggingface_hub import DatasetCard

from agentenv_portsim import wind

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("hub_dataset", ROOT / "scripts/hub_dataset.py")
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)
REFS = {r["task_id"]: r for r in wind.references()}
WEATHERS = {json.loads(line)["id"]: json.loads(line) for line in hub.WEATHER.read_text().splitlines()}
FILM = "dock-24B-w37x1-standard-0-e01"
BUST = "dock-24B-w07x1-busy-0-e04"
TAG = f"v{tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']['version']}"
PLUGIN = f"agentenv-portsim @ git+https://github.com/earakely-scale/agentenv-portsim-plugin@{TAG}"


def test_a_wind_week_row_carries_its_weather_week_and_the_forecasts_in_its_watches():
    task = wind.pack().get(FILM)
    row = hub.task_row(task, "v4", REFS[FILM], "{}", WEATHERS)
    assert (row["weather_week"], row["weather_kind"]) == ("2023-W10", "storm")
    assert row["schedule"] == "dock-24B-w37x1-standard-0"
    assert (row["optimal_cost"], row["hindsight_cost"], row["v3_optimal_cost"]) == (252, 359, 229)
    assert {"start": 122, "end": 135, "above_kn": 25, "unvalidated": 0.0} in json.loads(row["wind_windows"])
    senders = [n["from"] for w in json.loads(row["watches"]) for n in w["notices"]]
    assert senders.count("Barcelona Port Control") == row["num_watches"]
    assert row["situation"].rstrip().endswith("then call advance.") and "## Wind at the Dique Sur" in row["situation"]


def test_the_wind_references_keep_the_blind_re_planner_and_in_a_bust_week_the_hold_one():
    storm, bust = hub.reference_row(REFS[FILM]), hub.reference_row(REFS[BUST])
    assert storm["blind_feasible"] is False and "hold_cost" not in storm
    assert (bust["kind"], bust["hold_cost"], bust["rolling_cost"]) == ("bust", 242, 226)
    assert json.loads(bust["clauses"]) == {"a": True, "b": True, "c": True, "d": True}


def test_messages_are_typed_as_agentenv_hf_types_a_transcript():
    call = {"id": "c1", "type": "function", "function": {"name": "check_plan", "arguments": '{"plan": []}'}}
    record = {"messages": [{"role": "user", "content": "hi"},
                           {"role": "assistant", "content": None, "tool_calls": [call]},
                           {"role": "tool", "tool_call_id": "c1", "name": "check_plan", "content": "{}"}]}
    table = pq.read_table(io.BytesIO(hub.table_bytes([{"task_id": "t", "messages": hub.to_messages(record)}])))
    assert table.schema.field("messages").type == pa.list_(hub.tables.MESSAGE)
    [message] = [m for m in table.column("messages").to_pylist()[0] if m["tool_calls"]]
    assert json.loads(message["tool_calls"][0])["function"]["arguments"] == {"plan": []}


def test_the_card_lists_every_bundle_for_agent_env_hf_run_with_the_wind_port_first():
    data = DatasetCard(hub.card_text(PLUGIN)).data.to_dict()
    assert data["agentenv"]["default"] == "dock-v1-eval-wind"
    assert data["agentenv"]["bundles"] == {name: {"plugins": [PLUGIN], "setup": "agent-env portsim setup --agent"}
                                          for name in hub.BUNDLES.values()}
    names = [c["config_name"] for c in data["configs"]]
    assert names[0] == "v4_tasks" and [c for c in data["configs"] if c.get("default")] == [data["configs"][0]]
    assert {f"{n}_{t}" for n in hub.BUNDLES.values() for t in ("tasks", "episodes")} <= set(names)
    assert {"rl-environment", "agentenv"} <= set(data["tags"])


def test_the_hub_sources_install_this_version_of_the_plugin():
    assert f"agentenv-portsim-plugin/archive/refs/tags/{TAG}.tar.gz" in (ROOT / "hub/space/Dockerfile").read_text()
    for card in ("hub/dataset/README.md", "hub/space/README.md"):
        pins = {line.split("@")[-1].strip('"') for line in (ROOT / card).read_text().splitlines()
                if "agentenv-portsim-plugin@" in line}
        assert pins == {TAG}, card
