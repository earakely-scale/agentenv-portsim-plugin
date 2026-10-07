"""`agent-env portsim record`: one recorded episode filmed on the viewer, frame by frame in headless Chrome over the
DevTools protocol, into an MP4 (and a GIF). Each frame's step and hour come from the timeline alone."""

import base64
import itertools
import json
import math
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import NamedTuple
from urllib.parse import quote

import click
from websockets.sync.client import connect

from . import twin
from .episodes import Runs
from .sweep import RUNS
from .view import serve

CHROMES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "google-chrome", "google-chrome-stable",
           "chromium", "chromium-browser"]
VIEWS = ["overview", "harbour", "quayside", "overhead"]
LAYOUTS = ["full", "scene"]
ANSWER_SECONDS = 120


class Frame(NamedTuple):
    step: int
    hour: float


def _sweep(step: int, start: float, end: float, seconds: float, fps: int) -> list[Frame]:
    n = max(1, math.ceil(seconds * fps))
    return [Frame(step, start + (end - start) * (i + 1) / n) for i in range(n)]


def _hold(step: int, hour: float, seconds: float, fps: int) -> list[Frame]:
    return [Frame(step, hour)] * max(1, round(seconds * fps))


def timeline(rollout: dict, horizon: float, *, fps: int = 30, step_seconds: float = 2.5,
             hours_per_second: float = 6, intro_seconds: float = 2, outro_seconds: float = 3) -> list[Frame]:
    """v1: each plan held at hour 0, then the week played on the last one. A live week: each step held at its watch;
    an advance runs the clock to the watch it opens first; then the rest of the week."""
    steps = rollout["steps"]
    frames = _hold(0, 0, intro_seconds, fps)
    hour = 0
    for k, step in enumerate(steps):
        if "live" in rollout and step["hour"] > hour:
            frames += _sweep(k, hour, step["hour"], (step["hour"] - hour) / hours_per_second, fps)
            hour = step["hour"]
        frames += _hold(k, hour, step_seconds, fps)
    last = max(len(steps) - 1, 0)
    frames += _sweep(last, hour, horizon, (horizon - hour) / hours_per_second, fps)
    return frames + _hold(last, horizon, outro_seconds, fps)


def chrome_args(chrome: str, profile: Path, width: int, height: int) -> list[str]:
    return [chrome, "--headless=new", "--remote-debugging-port=0", f"--user-data-dir={profile}",
            f"--window-size={width},{height}", "--hide-scrollbars", "--mute-audio", "--no-first-run",
            "--disable-smooth-scrolling", "--force-device-scale-factor=1", "--enable-unsafe-swiftshader",
            "about:blank"]


def ffmpeg_args(ffmpeg: str, out: Path, fps: int, title: str) -> list[str]:
    return [ffmpeg, "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-vf", "scale=out_range=tv:out_color_matrix=bt709",
            "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-movflags", "+faststart", "-metadata", f"title={title}", "-metadata", f"comment={twin.ATTRIBUTION}",
            str(out)]


def gif_args(ffmpeg: str, mp4: Path, gif: Path) -> list[str]:
    return [ffmpeg, "-v", "error", "-y", "-i", str(mp4), "-vf",
            "fps=10,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];"
            "[b][p]paletteuse=dither=bayer:bayer_scale=3", "-loop", "0", str(gif)]


def find_chrome(path: str | None) -> str:
    for candidate in [path] if path else CHROMES:
        if found := shutil.which(candidate):
            return found
    raise click.ClickException(f"no Chrome found{f' at {path}' if path else ''}: pass --chrome PATH")


def find_ffmpeg() -> str:
    if found := shutil.which("ffmpeg"):
        return found
    raise click.ClickException("no ffmpeg on PATH")


class Page:
    """One page target over the DevTools protocol."""

    def __init__(self, ws):
        self.ws = ws
        self.ids = itertools.count(1)

    def call(self, method: str, **params) -> dict:
        i = next(self.ids)
        self.ws.send(json.dumps({"id": i, "method": method, "params": params}))
        try:
            while (message := json.loads(self.ws.recv(timeout=ANSWER_SECONDS))).get("id") != i:
                pass
        except TimeoutError as e:
            raise click.ClickException(f"Chrome did not answer {method} in {ANSWER_SECONDS} s; did the page load? "
                                       "The viewer loads three.js from jsDelivr.") from e
        if "error" in message:
            raise click.ClickException(f"{method}: {message['error']}")
        return message["result"]

    def js(self, expression: str):
        result = self.call("Runtime.evaluate", expression=expression, awaitPromise=True, returnByValue=True)
        if "exceptionDetails" in result:
            details = result["exceptionDetails"]
            error = details.get("exception", {}).get("description", details["text"])
            raise click.ClickException(f"{expression}: {error}")
        return result["result"].get("value")


def _devtools(profile: Path, chrome: subprocess.Popen) -> str:
    port_file = profile / "DevToolsActivePort"
    deadline = time.monotonic() + 30
    while not port_file.is_file():
        if chrome.poll() is not None or time.monotonic() > deadline:
            raise click.ClickException("Chrome did not start its DevTools server")
        time.sleep(0.05)
    port = port_file.read_text().split()[0]
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=10) as r:
        return next(t["webSocketDebuggerUrl"] for t in json.load(r) if t["type"] == "page")


@contextmanager
def recording(url: str, chrome: str, width: int, height: int) -> Iterator[tuple[Page, dict]]:
    """The page at ``url`` in headless Chrome, once ``portsim.ready``, and what it reports."""
    with tempfile.TemporaryDirectory() as profile:
        browser = subprocess.Popen(chrome_args(chrome, Path(profile), width, height), stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        try:
            with connect(_devtools(Path(profile), browser), max_size=None) as ws:
                page = Page(ws)
                page.call("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=1,
                          mobile=False)
                page.call("Page.navigate", url=url)
                page.js("new Promise(r => { const f = () => window.portsim ? r() : setTimeout(f, 50); f(); })")
                yield page, page.js("portsim.ready")
        finally:
            browser.terminate()
            browser.wait()


def record(url: str, rollout: dict, out: Path, *, chrome: str, ffmpeg: str, width: int, height: int, fps: int,
           view: str, pace: dict) -> int:
    """Films the rollout page at ``url``; returns the number of frames."""
    with recording(url, chrome, width, height) as (page, ready):
        if view != "overview":
            page.js(f"portsim.view({json.dumps(view)})")
        frames = timeline(rollout, ready["horizon"], fps=fps, **pace)
        title = f"{rollout['model']} · {rollout['task_id']} · {rollout['run']}"
        encoder = subprocess.Popen(ffmpeg_args(ffmpeg, out, fps, title), stdin=subprocess.PIPE)
        shown = None
        for frame in frames:
            if frame.step != shown:
                page.js(f"portsim.show({frame.step})")
                shown = frame.step
            page.js(f"portsim.time({frame.hour})")
            shot = page.call("Page.captureScreenshot", format="jpeg", quality=92)["data"]
            encoder.stdin.write(base64.b64decode(shot))
        encoder.stdin.close()
        if encoder.wait():
            raise click.ClickException(f"ffmpeg exited {encoder.returncode}")
    return len(frames)


def episode_url(port: int, run: str, model: str, task_id: str, layout: str = "full") -> str:
    return (f"http://127.0.0.1:{port}/viewer/?embed=1&record=1{'&layout=scene' if layout == 'scene' else ''}"
            f"#/run/{quote(run, safe='')}/{quote(model, safe='')}/{quote(task_id, safe='')}")


@click.command("record")
@click.option("--sweep", "sweep_name", required=True, help="Sweep under results/runs.")
@click.option("--model", required=True, help="Model id as the sweep ran it, e.g. anthropic/claude-sonnet-5-5.")
@click.option("--task", "task_id", required=True, help="Task id.")
@click.option("--out", required=True, type=click.Path(dir_okay=False, path_type=Path), help="MP4 to write.")
@click.option("--rep", default=1, show_default=True)
@click.option("--size", default="1920x1080", show_default=True, help="Frame size, WIDTHxHEIGHT.")
@click.option("--fps", default=30, show_default=True)
@click.option("--step-seconds", default=2.5, show_default=True, help="How long each step is held.")
@click.option("--hours-per-second", default=6.0, show_default=True, help="How fast time runs on the quay.")
@click.option("--intro-seconds", default=2.0, show_default=True)
@click.option("--outro-seconds", default=3.0, show_default=True)
@click.option("--view", type=click.Choice(VIEWS), default="overview", show_default=True, help="Camera view.")
@click.option("--layout", type=click.Choice(LAYOUTS), default="full", show_default=True,
              help="full: the viewer's page; scene: the 3D quay alone, with the watch panel over it.")
@click.option("--gif", type=click.Path(dir_okay=False, path_type=Path), help="Also write an 800 px GIF here.")
@click.option("--chrome", help="Chrome or Chromium binary. Default: Google Chrome, else chromium on PATH.")
def record_command(sweep_name, model, task_id, out, rep, size, fps, step_seconds, hours_per_second, intro_seconds,
                   outro_seconds, view, layout, gif, chrome):
    """Film one recorded episode on the viewer: each plan on the 3D quay and the dock chart, then the week played out;
    a live week watch by watch, with the clock running between watches. Every frame carries the OpenStreetMap
    attribution."""
    runs = Runs(RUNS, [sweep_name])
    k = next(iter(runs.runs.values())).sweep.k
    run = sweep_name if k == 1 else f"{sweep_name}.r{rep}"
    if run not in runs.runs or (model, task_id) not in runs.runs[run].rows:
        raise click.UsageError(f"no scored episode of {model} on {task_id} in {run}")
    width, height = (int(v) for v in size.lower().split("x"))
    chrome, ffmpeg = find_chrome(chrome), find_ffmpeg()
    server = serve(runs, twin.ensure(), 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = episode_url(server.server_port, run, model, task_id, layout)
    click.echo(twin.ATTRIBUTION)
    pace = {"step_seconds": step_seconds, "hours_per_second": hours_per_second, "intro_seconds": intro_seconds,
            "outro_seconds": outro_seconds}
    try:
        n = record(url, runs.rollout(run, model, task_id), out, chrome=chrome, ffmpeg=ffmpeg, width=width,
                   height=height, fps=fps, view=view, pace=pace)
    finally:
        server.shutdown()
    click.echo(f"Wrote {out}: {n} frames, {n / fps:.1f} s")
    if gif:
        subprocess.run(gif_args(ffmpeg, out, gif), check=True)
        click.echo(f"Wrote {gif}")
