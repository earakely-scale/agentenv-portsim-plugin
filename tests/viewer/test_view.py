"""The viewer's server: upstream's /api routes on the recorded runs, the vendored viewer behind our index.html, and the
twin from the cache, loopback only."""

import json
import re
import shutil
import socket
import threading
import urllib.request
from urllib.parse import quote

import pytest
from click.testing import CliRunner
from recorded import ROOT, SONNET

from agentenv_portsim import twin, view
from agentenv_portsim.episodes import Runs
from agentenv_portsim.sweep import PUBLISHED
from agentenv_portsim.view import EXT, UPSTREAM, route, serve

TASK = {"task_id", "split", "quay", "terminal", "week", "difficulty", "ships", "disruptions"}
RUN = {"run", "models", "episodes", "mean_reward", "env", "sweep", "rep", "k", "episode_cap_usd", "failed"}
BUSY = "dock-24B-w06x1-busy-0"


@pytest.fixture
def get(runs, tmp_path):
    (tmp_path / "twin.json.gz").write_bytes(b"\x1f\x8b gzip bytes")
    return lambda path: route(runs, tmp_path, path)


def body(response) -> object:
    status, headers, data = response
    assert (status, headers["Content-Type"]) == (200, "application/json")
    return json.loads(data)


def import_map(html: bytes) -> dict:
    return json.loads(re.search(rb'<script type="importmap">(.*?)</script>', html, re.S)[1])["imports"]


def test_config_is_explorer_mode_with_the_published_model_ids(get):
    assert body(get("/api/config")) == {"mode": "explorer", "published": PUBLISHED}


def test_tasks_are_the_weeks_with_episodes_and_a_task_is_its_public_form(get, runs):
    listed = body(get("/api/tasks"))
    assert [t["task_id"] for t in listed] == sorted(
        [BUSY, "dock-24B-w35x2-storm-0", "dock-36A-w06x1-standard-0", "dock-36A-w15x2-storm-0"])
    assert all(set(t) == TASK for t in listed)
    task = body(get(f"/api/tasks/{BUSY}"))
    assert task == runs.pack.public(runs.pack.get(BUSY)) and "reference" not in task
    assert body(get(f"/api/tasks/{BUSY}/reference")) == runs.pack.get(BUSY).reference


def test_runs_list_each_sweep_and_a_run_its_episodes(get, runs):
    listed = body(get("/api/runs"))
    assert [r["run"] for r in listed] == ["g2", "live-gpt", "live-sonnet"]
    assert all(set(r) == RUN for r in listed)
    assert listed[0] | {"mean_reward": None} == {"run": "g2", "models": [SONNET], "episodes": 3, "mean_reward": None,
                                                 "env": "portsim", "sweep": "g2", "rep": 1, "k": 1,
                                                 "episode_cap_usd": 2.0, "failed": []}
    assert body(get("/api/runs/live-sonnet")) == {"run": "live-sonnet", "episodes": runs.episodes("live-sonnet")}
    episode = f"/api/runs/live-sonnet/episode?model={quote(SONNET, safe='')}&task_id={BUSY}"
    assert body(get(episode)) == runs.rollout("live-sonnet", SONNET, BUSY)


def test_an_episode_that_no_longer_replays_is_listed_with_its_error_and_the_rest_stay(tmp_path):
    for run in ("g2", "live-sonnet"):
        shutil.copytree(ROOT / run, tmp_path / run)
    [path] = (tmp_path / "live-sonnet/transcripts").rglob("*.json")
    record = json.loads(path.read_text())
    tool = next(m for m in record["messages"] if m.get("name") == "check_plan")
    tool["content"] = tool["content"].replace('"cost":15', '"cost":14')
    path.write_text(json.dumps(record))
    runs = Runs(tmp_path)
    listed = body(route(runs, tmp_path, "/api/runs"))
    assert [(r["run"], r["episodes"], r["mean_reward"]) for r in listed][1] == ("live-sonnet", 0, None)
    [failed] = listed[1]["failed"]
    assert (failed["model"], failed["task_id"]) == (SONNET, BUSY) and failed["error"].startswith("check_plan")
    assert listed[0]["episodes"] == 3 and listed[0]["failed"] == []
    status, headers, data = route(runs, tmp_path, f"/api/runs/live-sonnet/episode?model={SONNET}&task_id={BUSY}")
    assert (status, headers["Content-Type"], json.loads(data)) == (500, "application/json", {"error": failed["error"]})


def test_the_twin_is_served_from_a_cache_under_a_symlink(runs, tmp_path):
    (tmp_path / "real").mkdir()
    (tmp_path / "real/cover.png").write_bytes(b"png")
    (tmp_path / "link").symlink_to(tmp_path / "real")
    assert route(runs, tmp_path / "link", "/viewer/twin/cover.png")[:2] == (200, {"Content-Type": "image/png"})


def test_a_port_in_use_is_a_usage_error(monkeypatch, tmp_path):
    monkeypatch.setattr(view, "RUNS", ROOT)
    monkeypatch.setattr(view.twin, "ensure", lambda: tmp_path)
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        port = busy.getsockname()[1]
        result = CliRunner().invoke(view.view_command, ["g2", "--port", str(port)])
    assert result.exit_code == 2 and f"can't serve on port {port}" in result.output


def test_the_viewer_is_upstreams_behind_our_index_with_three_modules_swapped(get):
    status, headers, html = get("/viewer/")
    assert (status, headers["Content-Type"]) == (200, "text/html; charset=utf-8")
    assert html == get("/viewer/index.html")[2] == (EXT / "index.html").read_bytes()
    ours, upstream = import_map(html), import_map((UPSTREAM / "index.html").read_bytes())
    assert ours == upstream | {"./stage.js": "./ext/stage.js", "./transcript.js": "./ext/transcript.js",
                               "./overview.js": "./ext/overview.js"}
    assert get("/viewer/app.js") == (200, {"Content-Type": "text/javascript; charset=utf-8"},
                                     (UPSTREAM / "app.js").read_bytes())
    assert get("/viewer/stage.js?v=cargo-4")[2] == (UPSTREAM / "stage.js").read_bytes()
    assert get("/viewer/ext/live.js")[2] == (EXT / "live.js").read_bytes()
    assert get("/viewer/twin/SOURCES.md")[0] == 200
    assert get("/")[:2] == get("/viewer")[:2] == (302, {"Location": "/viewer/"})


def test_the_twin_comes_from_the_cache_as_raw_gzip(get, tmp_path):
    status, headers, data = get("/viewer/twin/twin.json.gz")
    assert (status, headers, data) == (200, {"Content-Type": "application/gzip"}, b"\x1f\x8b gzip bytes")
    assert get("/viewer/twin/terrain.png")[0] == 404


@pytest.mark.parametrize("path", [
    "/viewer/../pyproject.toml", "/viewer/%2e%2e/%2e%2e/%2e%2e/pyproject.toml", "/viewer/ext/../../view.py",
    "/viewer/fixtures/tasks.json", "/viewer/dev_server.py", "/viewer/twin/", "/api/tasks/nope",
    "/api/tasks/nope/reference", "/api/runs/nope", "/api/runs/nope/episode?model=x&task_id=y",
    f"/api/runs/g2/episode?model=nope&task_id={BUSY}", f"/api/runs/g2/episode?model={SONNET}&task_id=nope",
    "/api/runs/g2/episode", "/api/episodes", "/healthz",
])
def test_anything_else_is_not_found(get, path):
    assert get(path)[0] == 404


def test_the_server_binds_the_host_it_is_given(runs, tmp_path):
    server = serve(runs, tmp_path, 0, "0.0.0.0")
    try:
        assert server.server_address[0] == "0.0.0.0"
    finally:
        server.server_close()


def test_the_server_answers_on_loopback(runs, tmp_path):
    server = serve(runs, tmp_path, 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        assert server.server_address[0] == "127.0.0.1"
        with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/api/runs", timeout=10) as response:
            assert response.headers["Cache-Control"] == "no-cache"
            assert response.headers["Content-Encoding"] is None
            assert [r["run"] for r in json.load(response)] == ["g2", "live-gpt", "live-sonnet"]
    finally:
        server.shutdown()
        server.server_close()


def test_the_twin_files_are_the_ones_the_viewer_loads():
    loaded = re.findall(r'"([a-z]+\.(?:json\.gz|png|webp))"', (UPSTREAM / "twin.js").read_text())
    assert sorted(set(loaded)) == sorted(twin.FILES)
