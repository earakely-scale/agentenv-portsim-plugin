"""The portsim bundle: installed, checked as `agent-env run` checks it, and its wiring tasks' plans graded."""

import json
from importlib.resources import files
from pathlib import Path

import pytest
from agent_env.bundle.installed import checked, find_bundle
from agent_env.bundle.parse import BundleKind
from agent_env.cli import cli
from agent_env.task_step.registry import get_task_step_registry
from berth_core import TaskPack, grade, parse_plan
from click.testing import CliRunner

ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "dock-24B-w07x1-busy-0"


def steps(task: str) -> list[dict]:
    return json.loads(files("agentenv_portsim.bundles").joinpath(f"portsim/tasks/{task}.json").read_text())


def submitted(task: str) -> list[dict]:
    return [d["args"]["plan"] for s in steps(task) if s["type"] == "apply_server_config"
            for d in s["directives"] if d["uri"] == "urn:portsim:submit-plan/v1"]


def graded(plan: list[dict]):
    task = TaskPack([ROOT / "data/dock-v1-eval"]).get(TASK_ID)
    return grade(task, *parse_plan(task, plan))


def test_plugin_check_passes(local_stores):
    result = CliRunner().invoke(cli, ["plugin", "check"])
    assert result.exit_code == 0, result.output


def test_the_bundle_installs_its_tasks_and_the_verifier(local_stores):
    bundle = checked(find_bundle("portsim"))
    entries = {(e.kind, e.name): e for e in bundle.entries}
    assert bundle.description.startswith("PortSim: re-plan a disrupted week")
    assert sorted(name for kind, name in entries if kind is BundleKind.TASK) == [
        "smoke", "wiring-infeasible", "wiring-nosubmit"]
    assert entries[BundleKind.ARTIFACT, "portsim-verifier"].type == "file"


@pytest.mark.parametrize("task", ["smoke", "wiring-infeasible", "wiring-nosubmit"])
def test_each_task_loads_a_task_into_portsim_and_grades_it_with_the_reward(local_stores, task):
    registry = get_task_step_registry()
    built = [registry[s["type"]].from_dict(s) for s in steps(task)]
    assert {s.env_id for s in built} == {"portsim"}
    assert [s.type for s in built[:2]] == ["deploy_env", "apply_server_config"]
    assert steps(task)[1]["directives"] == [
        {"service": "portsim", "uri": "urn:portsim:load-task/v1", "args": {"task_id": TASK_ID}}]
    grade_step = built[-1]
    assert (grade_step.type, grade_step.file_artifact_id, grade_step.score_aggregator.value) == (
        "env_outcome_verifier", "portsim-verifier", "weighted_average")


def test_smoke_submits_the_stored_optimal_plan():
    [plan] = submitted("smoke")
    assert plan == TaskPack([ROOT / "data/dock-v1-eval"]).get(TASK_ID).reference["optimal_plan"]
    assert graded(plan).reward == 1.0


def test_wiring_infeasible_submits_a_plan_that_breaks_the_rules():
    [plan] = submitted("wiring-infeasible")
    result = graded(plan)
    assert not result.feasible and result.violations
    assert result.reward <= 0.2


def test_wiring_nosubmit_submits_nothing():
    assert submitted("wiring-nosubmit") == []
    assert [s["id"] for s in steps("wiring-nosubmit")] == ["deploy", "load-task", "grade"]
