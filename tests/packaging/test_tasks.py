"""`agent-env portsim tasks generate`: the eval bundle, its tasks' exact steps, and the bundle checks `agent-env run`
makes before it reads a store."""

import json
from importlib.resources import files
from pathlib import Path

import pytest
from agent_env.bundle.parse import BundleKind, parse_bundle
from agent_env.bundle.plan import check_bundle
from agent_env.bundle.resolve import resolve_bundle
from agent_env.task_step.registry import get_task_step_registry
from berth_core import rules, situation
from click.testing import CliRunner

from agentenv_portsim import tasks
from agentenv_portsim.cli import portsim

VERIFY = files("agentenv_portsim.bundles").joinpath("portsim/artifacts/portsim-verifier/verify.py").read_bytes()


@pytest.fixture(scope="module")
def bundle(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("bundle") / "dock-v1-eval"
    tasks.generate("dock-v1-eval", out)
    return out


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_the_bundle_holds_the_readme_the_verifier_and_a_task_per_eval_task(bundle, tmp_path):
    files_ = snapshot(bundle)
    names = [t.task_id for t in tasks.pack_tasks("dock-v1-eval")]
    assert sorted(files_) == sorted(["README.md", "artifacts/portsim-verifier/verify.py",
                                     *(f"tasks/{n}.json" for n in names)])
    assert len(names) == 50
    assert files_["artifacts/portsim-verifier/verify.py"] == VERIFY
    assert files_["README.md"].decode().splitlines() == [
        "PortSim dock-v1-eval: 50 tasks, each played by the portsim-llm agent and graded by portsim-verifier.", "",
        "The prompts are derived from PortSimEnv's dock-v1 task packs (CC BY-SA 4.0). Contains data from the Port de "
        "Barcelona open data portal."]
    again = tmp_path / "again"
    assert tasks.generate("dock-v1-eval", again) == names
    assert snapshot(again) == files_
    assert tasks.generate("dock-v1-eval", again) == names
    assert snapshot(again) == files_


def test_a_task_deploys_loads_plays_with_upstreams_prompts_and_limits_and_grades(bundle):
    task = next(t for t in tasks.pack_tasks("dock-v1-eval") if t.task_id == "dock-24B-w06x1-busy-0")
    text = (bundle / "tasks/dock-24B-w06x1-busy-0.json").read_text()
    assert text == json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n"
    assert json.loads(text) == [
        {"id": "deploy", "type": "deploy_env", "env_id": "portsim"},
        {"id": "load-task", "type": "apply_server_config", "env_id": "portsim",
         "directives": [{"service": "portsim", "uri": "urn:portsim:load-task/v1",
                         "args": {"task_id": "dock-24B-w06x1-busy-0"}}]},
        {"id": "deploy-agent", "type": "deploy_agent", "a2a_agent_id": "portsim-llm", "env_ids": ["portsim"],
         "env_vars": {"PORTSIM_MAX_COST_USD": "5"}},
        {"id": "play", "type": "prompt_agent", "prompt_id": "dock-24B-w06x1-busy-0",
         "system_prompt": rules(task, 10),
         "prompt": situation(task) + "\n\nMake the new berth plan. Use check_plan to test drafts, then call "
                                     "submit_plan with your final plan.",
         "max_turns": 12, "model_params": {"max_tokens": 32000}, "timeout_seconds": 7200},
        {"id": "grade", "type": "env_outcome_verifier", "env_id": "portsim", "file_artifact_id": "portsim-verifier",
         "verifier_id": "portsim", "score_aggregator": "weighted_average"},
    ]


def test_every_task_builds_and_the_folder_passes_the_checks_run_makes_before_a_store(bundle, local_stores):
    registry = get_task_step_registry()
    for path in sorted((bundle / "tasks").glob("*.json")):
        built = [registry[s["type"]].from_dict(s) for s in json.loads(path.read_text())]
        assert [s.type for s in built] == ["deploy_env", "apply_server_config", "deploy_agent", "prompt_agent",
                                           "env_outcome_verifier"]
    parsed = parse_bundle(bundle)
    check_bundle(resolve_bundle(parsed))
    assert parsed.description.startswith("PortSim dock-v1-eval: 50 tasks")
    kinds = [(e.kind, e.name) for e in parsed.entries]
    assert (BundleKind.ARTIFACT, "portsim-verifier") in kinds
    assert sum(kind is BundleKind.TASK for kind, _ in kinds) == 50


@pytest.mark.parametrize(("cap", "env_value"), [(5.0, "5"), (0.75, "0.75")])
def test_the_episode_cap_reaches_the_agent(tmp_path, cap, env_value):
    tasks.generate("dock-v1-eval", tmp_path, task_ids=["dock-36A-w35x1-standard-0"], episode_cap_usd=cap)
    assert [p.name for p in (tmp_path / "tasks").iterdir()] == ["dock-36A-w35x1-standard-0.json"]
    deploy_agent = json.loads((tmp_path / "tasks/dock-36A-w35x1-standard-0.json").read_text())[2]
    assert deploy_agent["env_vars"] == {"PORTSIM_MAX_COST_USD": env_value}


@pytest.mark.parametrize(("args", "out"), [([], "results/bundles/dock-v1-eval"), (["--out", "elsewhere"], "elsewhere")])
def test_generate_writes_to_out_or_results_bundles(tmp_path, monkeypatch, args, out):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(portsim, ["tasks", "generate", "--pack", "dock-v1-eval", *args])
    assert result.exit_code == 0, result.output
    assert result.output.startswith(f"Wrote 50 tasks into {out}; play one with: agent-env run {out} --task ")
    assert len(list((tmp_path / out / "tasks").iterdir())) == 50
