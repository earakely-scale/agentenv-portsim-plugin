"""The viewer's server: upstream's /api routes on the recorded runs, the vendored viewer behind our index.html, and the
twin from the cache, loopback only."""

import json
import re
import threading
import urllib.request
from urllib.parse import quote

import pytest
from recorded import SONNET

from agentenv_portsim import twin
from agentenv_portsim.sweep import PUBLISHED
from agentenv_portsim.view import EXT, UPSTREAM, route, serve

TASK = {"task_id", "split", "quay", "terminal", "week", "difficulty", "ships", "disruptions"}
RUN = {"run", "models", "episodes", "mean_reward", "env", "sweep", "rep", "k", "episode_cap_usd"}
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
                                                 "episode_cap_usd": 2.0}
    assert body(get("/api/runs/live-sonnet")) == {"run": "live-sonnet", "episodes": runs.episodes("live-sonnet")}
    episode = f"/api/runs/live-sonnet/episode?model={quote(SONNET, safe='')}&task_id={BUSY}"
    assert body(get(episode)) == runs.rollout("live-sonnet", SONNET, BUSY)


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
