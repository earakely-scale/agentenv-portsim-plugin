"""scripts/hub_dataset.py's rows, its typed transcripts and the card it writes for agent-env hf run, a dry build with
and without a lines sweep, and the Hub sources in hub/ pinned to this version."""

import importlib.util
import io
import json
import sys
import tomllib
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from agent_env.bundle.parse import parse_bundle
from agent_env.config import get_config
from agent_env.store.routing import namespace_routing
from agent_env.task.store import TASK_INSTANCES_COLLECTION
from huggingface_hub import DatasetCard

from agentenv_portsim import lines, tasks, wind

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("hub_dataset", ROOT / "scripts/hub_dataset.py")
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)
REFS = {r["task_id"]: r for r in wind.references()}
LINES_REFS = {r["task_id"]: r for r in lines.references()}
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


def test_a_lines_week_row_carries_its_wind_week_its_ships_agents_and_their_reports():
    task = lines.pack().get(FILM)
    row = hub.task_row(task, "v5", LINES_REFS[FILM], "{}", WEATHERS)
    assert (row["schedule"], row["weather_id"], row["weather_week"], row["weather_kind"]) == (
        "dock-24B-w37x1-standard-0", "e01", "2023-W10", "storm")
    assert row["wind_windows"] == hub.task_row(wind.pack().get(FILM), "v4", REFS[FILM], "{}", WEATHERS)["wind_windows"]
    assert row["v4_optimal_cost"] == REFS[FILM]["optimal_cost"] and "blind_cost" not in row
    agents = json.loads(row["agents"])
    deployed = [s["agent_name"] for s in tasks.lines_steps(task, 5.0) if s["id"].startswith("deploy-")
                and s.get("role") == "line"]
    assert [a["agent"] for a in agents] == deployed and row["num_agents"] == len(agents) == LINES_REFS[FILM]["firms"]
    assert sorted(s for a in agents for s in a["ships"]) == list(range(row["num_ships"]))
    notices = [n for w in json.loads(row["watches"]) for n in w["notices"]]
    assert sum(n["from"] == "Barcelona Port Control" for n in notices) == row["num_watches"]
    reports = [n["text"] for n in notices if n["from"] in {a["name"] for a in agents}]
    assert reports and all("ETA" in text or "calls in" in text for text in reports)
    assert "## Arrivals and the ships' agents" in row["situation"] and "message_agent" in row["system_prompt"]


def test_the_wind_references_keep_the_blind_re_planner_and_in_a_bust_week_the_hold_one_and_the_lines_their_own():
    storm, bust = hub.reference_row(REFS[FILM]), hub.reference_row(REFS[BUST])
    assert storm["blind_feasible"] is False and "hold_cost" not in storm
    assert (bust["kind"], bust["hold_cost"], bust["rolling_cost"]) == ("bust", 242, 226)
    assert json.loads(bust["clauses"]) == {"a": True, "b": True, "c": True, "d": True}
    assert not {"silent_cost", "rolling_anchor_hours", "rolling_exchanges"} & set(storm)
    week = hub.reference_row(LINES_REFS[FILM])
    assert not {"blind_cost", "hold_cost", "weather"} & set(week)
    assert week["hindsight_cost"] <= week["optimal_cost"] and week["wind_optimal_cost"] == REFS[FILM]["optimal_cost"]
    assert {f"{p}_anchor_hours" for p in ("rolling", "silent", "naive")} <= set(week) and "silent_feasible" in week
    assert {"watch", "ship", "agreed"} <= set(json.loads(week["rolling_exchanges"])[0])
    assert set(json.loads(week["clauses"])) == {"a", "b", "c"}


def test_a_sweep_takes_the_version_of_its_env_and_the_lines_sweeps_are_built_by_default():
    assert [hub.version_of(s) for s in ({"live": True, "lines": True}, {"live": True, "wind": True},
                                        {"live": True, "marine": True}, {"live": True}, {})] == [
        "v5", "v4", "v3", "v2", "v1"]
    assert {"lines-fix6-astra", "lines-r6-opus", "lines-r6-glm-j", "wind-gpt-2"} <= set(hub.SWEEPS)
    assert not {"lines-opus", "lines-r6-astra"} & set(hub.SWEEPS)
    assert (hub.BUNDLES["v5"], hub.ENVS["v5"], hub.LIVE_VERSIONS[0]) == ("dock-v1-eval-lines", "portsim-lines", "v5")


def test_messages_are_typed_as_agentenv_hf_types_a_transcript():
    call = {"id": "c1", "type": "function", "function": {"name": "check_plan", "arguments": '{"plan": []}'}}
    record = {"messages": [{"role": "user", "content": "hi"},
                           {"role": "assistant", "content": None, "tool_calls": [call]},
                           {"role": "tool", "tool_call_id": "c1", "name": "check_plan", "content": "{}"}]}
    table = pq.read_table(io.BytesIO(hub.table_bytes([{"task_id": "t", "messages": hub.to_messages(record)}])))
    assert table.schema.field("messages").type == pa.list_(hub.tables.MESSAGE)
    [message] = [m for m in table.column("messages").to_pylist()[0] if m["tool_calls"]]
    assert json.loads(message["tool_calls"][0])["function"]["arguments"] == {"plan": []}


def test_the_card_lists_every_bundle_for_agent_env_hf_run_with_the_lines_port_first():
    data = DatasetCard(hub.card_text(PLUGIN)).data.to_dict()
    assert data["agentenv"]["default"] == "dock-v1-eval-lines"
    assert data["agentenv"]["bundles"] == {name: {"plugins": [PLUGIN], "setup": "agent-env portsim setup --agent"}
                                          for name in hub.BUNDLES.values()}
    names = [c["config_name"] for c in data["configs"]]
    assert names[0] == "v5_tasks" and [c for c in data["configs"] if c.get("default")] == [data["configs"][0]]
    assert {f"v5_{t}" for t in ("tasks", "episodes", "references")} <= set(names)
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
    assert "At the anchor" in hub.board_markdown("v5", [kimi, luna], 2).splitlines()[0]
    assert hub.board_json("v5", [kimi, luna], 2)["env"] == "portsim-lines"


def test_the_summary_weighs_every_week_alike_and_leaves_out_a_model_missing_a_version_and_a_version_still_running():
    played = [("v4", "a", 0.5, 15), ("v3", "a", 1.0, 15), ("v2", "a", 1.0, 30), ("v4", "b", 0.9, 15),
              ("v3", "b", 0.9, 15), ("v2", "b", 0.9, 30), ("v4", "c", 1.0, 15), ("v1", "a", 0.0, 10)]
    rows = [{"version": v, "model": m, "model_name": m.upper(), "provider": "P", "mean_reward": mean, "weeks": weeks,
             "feasible": weeks} for v, m, mean, weeks in played]
    head, _, first, second = hub.summary_markdown(rows).splitlines()
    assert "v4, the wind port" in head and "All weeks" in head and "v5" not in head
    assert first.startswith("| B | P | 0.900 | 0.900 | 0.900 | **0.900** | 60 of 60")
    assert second.startswith("| A | P | 0.500 | 1.000 | 1.000 | **0.875** | 60 of 60")
    lines_b = {"version": "v5", "model": "b", "model_name": "B", "provider": "P", "mean_reward": 0.6, "weeks": 15,
               "feasible": 15}
    head, _, only = hub.summary_markdown([*rows, lines_b]).splitlines()
    assert head.startswith("| Model | Provider | v5, the lines port | v4, the wind port")
    assert only.startswith("| B | P | 0.600 | 0.900 | 0.900 | 0.900 | **0.840** | 75 of 75")
    running_a = lines_b | {"model": "a", "model_name": "A", "weeks": 9, "feasible": 9}
    head, _, *both = hub.summary_markdown([*rows, lines_b, running_a]).splitlines()
    assert "v5" not in head and len(both) == 2


def test_the_card_carries_each_versions_board_between_its_markers():
    text = hub.card_text(PLUGIN, {"v4": "| Kimi K3 |"})
    assert "<!-- board:v4 -->\n\n| Kimi K3 |\n\n<!-- /board:v4 -->" in text
    assert "<!-- board:v2 -->\n\n<!-- /board:v2 -->" in text and "<!-- board:v5 -->\n\n<!-- /board:v5 -->" in text
    assert text.index("<!-- board:v5 -->") < text.index("<!-- board:v4 -->")
    assert "results" in [c["config_name"] for c in DatasetCard(text).data.to_dict()["configs"]]


def test_the_hub_sources_install_this_version_of_the_plugin():
    assert f"agentenv-portsim-plugin/archive/refs/tags/{TAG}.tar.gz" in (ROOT / "hub/space/Dockerfile").read_text()
    for card in ("hub/dataset/README.md", "hub/space/README.md"):
        pins = {line.split("@")[-1].strip('"') for line in (ROOT / card).read_text().splitlines()
                if "agentenv-portsim-plugin@" in line}
        assert pins == {TAG}, card


OPUS = "anthropic/claude-opus-5-5"
PLAN = [{"ship": 0, "berth_hour": 4, "section": 13, "cranes": 4}]
EXCHANGES = [
    {"watch": 0, "hour": 0, "firm": "aperez", "ship": 1, "ask": "eta", "call": 1,
     "reply": {"ship": 1, "name": "MSC ALINA", "eta": 40, "as_of": 0}},
    {"watch": 0, "hour": 0, "firm": "aperez", "ship": 4, "ask": "request_arrival", "arrival": 60, "call": 1,
     "reply": {"ship": 4, "name": "MSC JADE", "agreed": True, "arrival": 60, "turn": 58, "slowing": True}},
]


def _lines_run(sweep: Path, instance: str) -> None:
    """One scored run of the film week in ``sweep``'s results.jsonl, as `agent-env portsim sweep run --lines` records
    it, with its transcript."""
    transcript = Path("transcripts/anthropic-claude-opus-5-5") / f"{FILM}-r1-a1.json"
    (sweep / transcript).parent.mkdir(parents=True)
    (sweep / transcript).write_text(json.dumps({"messages": [{"role": "user", "content": "hi"}], "steps": [],
                                                "final": {}, "seconds": 60.0}))
    row = {"sweep": sweep.name, "model": OPUS, "task_id": FILM, "rep": 1, "attempt": 1, "instance": instance,
           "outcome": "scored", "reward": 0.5, "submitted": True, "feasible": True, "plan_cost": 500,
           "optimal_cost": 407, "turns": 20, "tool_calls": 30, "input_tokens": 1000, "output_tokens": 100,
           "cost_usd": 0.5, "wall_seconds": 100.0, "end_reason": "done", "watches": 5, "regret": 93, "excused_cost": 0,
           "anchor_hours": 12, "messages": len(EXCHANGES), "transcript": transcript.as_posix()}
    (sweep / "results.jsonl").write_text(json.dumps(row) + "\n")


def test_a_lines_run_row_carries_its_hours_at_anchor_and_its_exchanges_with_the_ships_agents(tmp_path):
    sweep = tmp_path / "lines-opus"
    sweep.mkdir()
    _lines_run(sweep, "instance-1")
    graded = {"dock-v1-eval-lines/run-1": {"plan": PLAN, "lines": {"exchanges": EXCHANGES}}}
    [row] = hub.episode_rows(sweep, "v5", {FILM: lines.pack().get(FILM)}, {"instance-1": "dock-v1-eval-lines/run-1"},
                             graded)
    assert (row["anchor_hours"], row["agent_messages"], row["reached_end"]) == (12, 2, True)
    assert json.loads(row["exchanges"]) == EXCHANGES and json.loads(row["final_plan"]) == PLAN
    table = pq.read_table(io.BytesIO(hub.table_bytes([row])))
    assert table.schema.names[-1] == "messages" and table.schema.field("messages").type == pa.list_(hub.tables.MESSAGE)


def _dry_build(tmp_path, monkeypatch) -> Path:
    """`scripts/hub_dataset.py --runs <tmp>/runs --out <tmp>/out`, with no --repo."""
    out = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["hub_dataset.py", "--runs", str(tmp_path / "runs"), "--out", str(out)])
    hub.main()
    return out


def _rows(out: Path, path: str) -> list[dict]:
    return pq.read_table(out / path).to_pylist()


def test_a_dry_build_without_a_lines_sweep_has_the_lines_weeks_and_references_and_no_runs(
        local_stores, tmp_path, monkeypatch):
    (tmp_path / "runs").mkdir()
    out = _dry_build(tmp_path, monkeypatch)
    weeks = _rows(out, "tasks/v5.parquet")
    assert [w["task_id"] for w in weeks] == lines.task_ids() and all(json.loads(w["agents"]) for w in weeks)
    assert len(_rows(out, "tasks/dock-v1-eval-lines.parquet")) == 15
    assert len(list((out / "bundles/dock-v1-eval-lines/tasks").glob("*.json"))) == 15
    assert len(_rows(out, "references/lines.parquet")) == 15
    assert (out / "references/lines.jsonl").read_bytes() == lines.REFERENCES.read_bytes()
    assert _rows(out, "episodes/v5.parquet") == _rows(out, "episodes/dock-v1-eval-lines.parquet") == []
    assert not list((out / "results").glob("v*.json")) and _rows(out, "results/board.parquet") == []
    card = (out / "README.md").read_text()
    assert "<!-- board:v5 -->\n\n<!-- /board:v5 -->" in card and "<!-- board:all -->\n\n<!-- /board:all -->" in card
    assert DatasetCard(card).data.to_dict()["agentenv"]["default"] == "dock-v1-eval-lines"


def test_a_dry_build_with_a_lines_sweep_publishes_its_run_in_both_kinds_of_table_and_on_the_board(
        local_stores, tmp_path, monkeypatch):
    sweep = tmp_path / "runs/lines-r6-opus"
    sweep.mkdir(parents=True)
    (sweep / "sweep.json").write_text(json.dumps({"name": "lines-r6-opus", "models": [OPUS], "tasks": [FILM], "k": 1,
                                                  "episode_cap_usd": 5.0, "live": True, "lines": True}))
    tasks.generate(hub.EVAL_PACK, sweep / "bundle", task_ids=[FILM], lines=True)
    task_id = f"{parse_bundle(sweep / 'bundle').id_root}/{FILM}"
    instance = f"{task_id}-abcd1234"
    episode = {"done": True, "plan": PLAN, "lines": {"exchanges": EXCHANGES}}
    with namespace_routing():
        get_config().get_document_store().insert(TASK_INSTANCES_COLLECTION, {
            "instance_id": instance, "task_id": task_id, "task_version": 1, "status": "completed", "current_step": 13,
            "total_steps": 13, "created_at_utc": "2026-10-11 09:00 UTC", "completed_at_utc": "2026-10-11 09:20 UTC",
            "context": {"agent_model": OPUS, "prompt_responses": [{"step_id": "play", "model": OPUS, "response": "done",
                                                                   "tool_call_count": 30}],
                        "metadata": {"verifications": {"portsim": {"score": 0.5, "results": [
                            {"criterion": "the executed week's reward", "result": False, "score": 0.5,
                             "episode": episode}]}}}}})
    _lines_run(sweep, instance)
    out = _dry_build(tmp_path, monkeypatch)
    [run] = _rows(out, "episodes/v5.parquet")
    assert run["episode_id"].startswith("dock-v1-eval-lines/") and run["sweep"] == "lines-r6-opus"
    assert (run["anchor_hours"], run["agent_messages"], json.loads(run["exchanges"])) == (12, 2, EXCHANGES)
    [published] = _rows(out, "episodes/dock-v1-eval-lines.parquet")
    assert (published["episode_id"], published["reward"]) == (run["episode_id"], 0.5)
    assert len((out / "raw/dock-v1-eval-lines.jsonl").read_text().splitlines()) == 1
    board = json.loads((out / "results/v5.json").read_text())
    assert (board["env"], board["tasks"], board["board"][0]["model"]) == ("portsim-lines", 1, "Claude Opus 5.5")
    assert not (out / "results/v4.json").exists() and _rows(out, "episodes/v4.parquet") == []
    assert {"runs/lines-r6-opus/sweep.json", "runs/lines-r6-opus/results.jsonl"} <= {
        p.relative_to(out).as_posix() for p in out.rglob("*")}
    assert not (out / "runs/lines-r6-opus/bundle").exists()
    card = (out / "README.md").read_text()
    v5 = card.split("<!-- board:v5 -->")[1].split("<!-- /board:v5 -->")[0]
    assert "At the anchor" in v5 and "| Claude Opus 5.5 | Anthropic | 1 of 1 | **0.500**" in v5
    assert "| v5, the lines port | All weeks |" in card.split("<!-- board:all -->")[1]
