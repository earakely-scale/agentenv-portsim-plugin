"""`agent-env portsim view`: recorded sweeps replayed on PortSimEnv's viewer, served read-only on loopback with the
/api routes and JSON of its explorer (envs/berth_planning/openenv/berth_openenv/api.py at b0f4c2f)."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import click

from . import twin
from .episodes import ReplayError, Runs
from .sweep import PUBLISHED, RUNS

WEB = Path(__file__).resolve().parent / "web"
UPSTREAM, EXT = WEB / "upstream", WEB / "ext"
TYPES = {".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".html": "text/html; charset=utf-8", ".md": "text/markdown; charset=utf-8", ".png": "image/png",
         ".webp": "image/webp", ".gz": "application/gzip"}
NOT_FOUND = (404, {"Content-Type": "text/plain"}, b"not found")

Response = tuple[int, dict[str, str], bytes]
"""Status, headers and body: a redirect needs its Location."""


def _json(obj) -> Response:
    return 200, {"Content-Type": "application/json"}, json.dumps(obj, ensure_ascii=False).encode()


def _file(root: Path, name: str) -> Response:
    root = root.resolve()
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        return NOT_FOUND
    return 200, {"Content-Type": TYPES.get(path.suffix, "application/octet-stream")}, path.read_bytes()


def route(runs: Runs, twin_dir: Path, path: str) -> Response:
    url = urlsplit(path)
    parts = [unquote(p) for p in url.path.split("/") if p]
    query = {k: v[0] for k, v in parse_qs(url.query).items()}
    episode = (query.get("model"), query.get("task_id"))
    if url.path in ("/", "/viewer"):
        return 302, {"Location": "/viewer/"}, b""
    if url.path in ("/viewer/", "/viewer/index.html"):
        return _file(EXT, "index.html")
    match parts:
        case ["viewer", "ext", *rest]:
            return _file(EXT, "/".join(rest))
        case ["viewer", "twin", name] if name in twin.FILES:
            return _file(twin_dir, name)
        case ["viewer", *rest]:
            return _file(UPSTREAM, "/".join(rest))
        case ["api", "config"]:
            return _json({"mode": "explorer", "published": PUBLISHED})
        case ["api", "tasks"]:
            return _json(runs.tasks())
        case ["api", "tasks", task_id] if runs.has(task_id):
            return _json(runs.pack.public(runs.task(task_id)))
        case ["api", "tasks", task_id, "reference"] if runs.has(task_id):
            return _json(runs.task(task_id).reference)
        case ["api", "runs"]:
            return _json(runs.index())
        case ["api", "runs", run] if run in runs.runs:
            return _json({"run": run, "episodes": runs.episodes(run)})
        case ["api", "runs", run, "episode"] if run in runs.runs and episode in runs.runs[run].rows:
            try:
                return _json(runs.rollout(run, *episode))
            except ReplayError as e:
                return 500, {"Content-Type": "application/json"}, json.dumps({"error": str(e)}).encode()
    return NOT_FOUND


def serve(runs: Runs, twin_dir: Path, port: int, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            status, headers, body = route(runs, twin_dir, self.path)
            self.send_response(status)
            for key, value in (headers | {"Cache-Control": "no-cache", "Content-Length": str(len(body))}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    return ThreadingHTTPServer((host, port), Handler)


@click.command("view")
@click.argument("sweeps", nargs=-1)
@click.option("--port", default=8237, show_default=True, help="Port to serve on.")
@click.option("--host", default="127.0.0.1", show_default=True,
              help="Address to serve on: 0.0.0.0 for every interface, as in a container or a Space.")
def view_command(sweeps: tuple[str, ...], port: int, host: str):
    """Replay recorded sweeps (default: all under results/runs) on PortSimEnv's viewer: the 3D quay, the dock chart,
    each plan the agent checked or confirmed, the grade and the transcript; live weeks watch by watch."""
    runs = Runs(RUNS, list(sweeps) or None)
    if not runs.runs:
        raise click.UsageError(f"no sweeps under {RUNS}: run `agent-env portsim sweep run` first")
    twin_dir = twin.ensure()
    try:
        server = serve(runs, twin_dir, port, host)
    except OSError as e:
        raise click.UsageError(f"can't serve on port {port} ({e.strerror}): pass another --port") from e
    click.echo(twin.ATTRIBUTION)
    click.echo(f"Serving {', '.join(runs.runs)} at http://{host}:{server.server_port}/viewer/ (Ctrl-C to stop)")
    threading.Thread(target=runs.index, daemon=True).start()  # replaying every live week takes a minute; start now
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
