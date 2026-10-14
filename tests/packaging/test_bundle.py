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
TRAIN_TASK_ID = "dock-24B-w04x1-standard-2"
LOADS = {"smoke": TASK_ID, "wiring-infeasible": TASK_ID, "wiring-nosubmit": TASK_ID,
         "smoke-train": TRAIN_TASK_ID, "wiring-nosubmit-train": TRAIN_TASK_ID}


def steps(task: str) -> list[dict]:
    return json.loads(files("agentenv_portsim.bundles").joinpath(f"portsim/tasks/{task}.json").read_text())


def submitted(task: str) -> list[dict]:
    return [d["args"]["plan"] for s in steps(task) if s["type"] == "apply_server_config"
            for d in s["directives"] if d["uri"] == "urn:portsim:submit-plan/v1"]


def pack_task(task_id: str):
    return TaskPack([ROOT / "data/dock-v1-eval", ROOT / "data/dock-v1-train"]).get(task_id)


def graded(plan: list[dict], task_id: str = TASK_ID):
    task = pack_task(task_id)
    return grade(task, *parse_plan(task, plan))


def test_plugin_check_passes(local_stores):
    result = CliRunner().invoke(cli, ["plugin", "check"])
    assert result.exit_code == 0, result.output


def test_the_bundle_installs_its_tasks_and_the_verifier(local_stores):
    bundle = checked(find_bundle("portsim"))
    entries = {(e.kind, e.name): e for e in bundle.entries}
    assert bundle.description.startswith("PortSim: re-plan a disrupted week")
    assert sorted(name for kind, name in entries if kind is BundleKind.TASK) == sorted(LOADS)
    assert entries[BundleKind.ARTIFACT, "portsim-verifier"].type == "file"


@pytest.mark.parametrize("task", sorted(LOADS))
def test_each_task_loads_a_task_into_portsim_and_grades_it_with_the_reward(local_stores, task):
    registry = get_task_step_registry()
    built = [registry[s["type"]].from_dict(s) for s in steps(task)]
    assert {s.env_id for s in built} == {"portsim"}
    assert [s.type for s in built[:2]] == ["deploy_env", "apply_server_config"]
    assert steps(task)[1]["directives"] == [
        {"service": "portsim", "uri": "urn:portsim:load-task/v1", "args": {"task_id": LOADS[task]}}]
    grade_step = built[-1]
    assert (grade_step.type, grade_step.file_artifact_id, grade_step.score_aggregator.value) == (
        "env_outcome_verifier", "portsim-verifier", "weighted_average")


@pytest.mark.parametrize("task", ["smoke", "smoke-train"])
def test_smoke_submits_the_stored_optimal_plan(task):
    [plan] = submitted(task)
    assert plan == pack_task(LOADS[task]).reference["optimal_plan"]
    assert graded(plan, LOADS[task]).reward == 1.0


def test_the_train_tasks_load_a_standard_train_task():
    assert pack_task(TRAIN_TASK_ID).difficulty == "standard"
    assert TRAIN_TASK_ID not in {t.task_id for t in TaskPack([ROOT / "data/dock-v1-eval"]).tasks}


def test_wiring_infeasible_submits_a_plan_that_breaks_the_rules():
    [plan] = submitted("wiring-infeasible")
    result = graded(plan)
    assert not result.feasible and result.violations
    assert result.reward <= 0.2


@pytest.mark.parametrize("task", ["wiring-nosubmit", "wiring-nosubmit-train"])
def test_wiring_nosubmit_submits_nothing(task):
    assert submitted(task) == []
    assert [s["id"] for s in steps(task)] == ["deploy", "load-task", "grade"]
