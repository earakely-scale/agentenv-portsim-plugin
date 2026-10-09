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


def _run(model, task_id, reward, tier="busy", feasible=True, cost=300, reached=True, usd=0.5):
    return {"model": model, "task_id": task_id, "difficulty": tier, "reward": reward, "feasible": feasible,
            "cost": cost, "optimal_cost": 300, "turns": 10, "input_tokens": 1000, "output_tokens": 100,
            "cost_usd": usd, "seconds": 60.0, "reached_end": reached}


def test_the_board_ranks_models_by_their_mean_over_weeks_with_each_tier_and_portsim_envs_counts():
    runs = [_run("openai/gpt-6-luna", "a", 0.2, feasible=False, cost=900, reached=False, usd=None),
            _run("openai/gpt-6-luna", "b", 0.4, tier="standard", cost=320),
            _run("fireworks_ai/kimi-k3", "a", 1.0), _run("fireworks_ai/kimi-k3", "a", 0.8),
            _run("fireworks_ai/kimi-k3", "b", 0.6, tier="standard", cost=310)]
    kimi, luna = hub.board("v4", runs)
    assert (kimi["model_name"], kimi["provider"], kimi["weeks"], kimi["runs"]) == ("Kimi K3", "Fireworks", 2, 3)
    assert kimi["mean_reward"] == 0.75 and kimi["ci_low"] <= 0.75 <= kimi["ci_high"]
    assert (kimi["reward_busy"], kimi["reward_standard"], kimi["optimal"]) == (0.9, 0.6, 2)
    assert (luna["finished"], luna["feasible"], luna["optimal"], luna["cost_usd"]) == (1, 1, 0, 0.5)
    board = hub.board_json("v4", [kimi, luna], 2)
    assert board["env"] == "portsim-wind" and board["board"][0]["tiers"] == {"standard": 0.6, "busy": 0.9}
    assert {"model", "key", "n", "mean", "tiers", "submitted", "feasible", "optimal", "tokens_out", "tokens_in",
            "median_s"} <= set(board["board"][1])
    table = hub.board_markdown("v4", [kimi, luna], 2).splitlines()
    assert "At the anchor" in table[0] and table[2].startswith("| Kimi K3 | Fireworks | 2 of 2 | **0.750**")


def test_the_summary_weighs_every_week_alike_and_leaves_out_a_model_missing_a_version():
    played = [("v4", "a", 0.5, 15), ("v3", "a", 1.0, 15), ("v2", "a", 1.0, 30), ("v4", "b", 0.9, 15),
              ("v3", "b", 0.9, 15), ("v2", "b", 0.9, 15), ("v4", "c", 1.0, 15), ("v1", "a", 0.0, 10)]
    rows = [{"version": v, "model": m, "model_name": m.upper(), "provider": "P", "mean_reward": mean, "weeks": weeks,
             "feasible": weeks} for v, m, mean, weeks in played]
    head, _, first, second = hub.summary_markdown(rows).splitlines()
    assert "v4, the wind port" in head and "All weeks" in head
    assert first.startswith("| B | P | 0.900 | 0.900 | 0.900 | **0.900** | 45 of 45")
    assert second.startswith("| A | P | 0.500 | 1.000 | 1.000 | **0.875** | 60 of 60")


def test_the_card_carries_each_versions_board_between_its_markers():
    text = hub.card_text(PLUGIN, {"v4": "| Kimi K3 |"})
    assert "<!-- board:v4 -->\n\n| Kimi K3 |\n\n<!-- /board:v4 -->" in text
    assert "<!-- board:v2 -->\n\n<!-- /board:v2 -->" in text
    assert "results" in [c["config_name"] for c in DatasetCard(text).data.to_dict()["configs"]]


def test_the_hub_sources_install_this_version_of_the_plugin():
    assert f"agentenv-portsim-plugin/archive/refs/tags/{TAG}.tar.gz" in (ROOT / "hub/space/Dockerfile").read_text()
    for card in ("hub/dataset/README.md", "hub/space/README.md"):
        pins = {line.split("@")[-1].strip('"') for line in (ROOT / card).read_text().splitlines()
                if "agentenv-portsim-plugin@" in line}
        assert pins == {TAG}, card
