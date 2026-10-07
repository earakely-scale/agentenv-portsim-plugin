"""The film's timeline, the Chrome and ffmpeg command lines, and (with Chrome, ffmpeg and the network) a short take and
a live week that shows no news before its bulletin."""

import json
import re
import shutil
import subprocess
import threading

import click
import pytest
from click.testing import CliRunner
from recorded import LIVE, ROOT, SONNET

from agentenv_portsim import record, twin
from agentenv_portsim.record import Frame, Page, chrome_args, ffmpeg_args, gif_args, timeline
from agentenv_portsim.view import serve

PACE = {"fps": 10, "step_seconds": 1, "hours_per_second": 20, "intro_seconds": 1, "outro_seconds": 2}
SHOWN = """import("/viewer/ext/stage.js").then(({ currentStage }) => {
  const { chart, scene } = currentStage();
  const text = (selector) => document.querySelector(selector).innerText;
  return { task: chart.task, scene: scene.task === chart.task, drawn: [...chart.shipEls.keys()],
           afloat: [...scene.actors.values()].filter((a) => a.ship).map((a) => a.id),
           winds: chart.svg.querySelectorAll("g.wind").length, outages: chart.svg.querySelectorAll("g.outage").length,
           panel: text(".ps-watch") + text(".ps-chip"), transcript: text("#transcript") };
})"""


def hours(frames: list[Frame]) -> list[float]:
    return [f.hour for f in frames]


def test_a_v1_film_holds_each_plan_at_hour_0_then_plays_the_week_on_the_last():
    frames = timeline({"steps": [{}, {}, {}]}, 100, **PACE)
    assert frames[:10] == [Frame(0, 0)] * 10
    assert frames[10:40] == [Frame(0, 0)] * 10 + [Frame(1, 0)] * 10 + [Frame(2, 0)] * 10
    assert frames[40:90] == [Frame(2, 100 * i / 50) for i in range(1, 51)]
    assert frames[90:] == [Frame(2, 100)] * 20


def test_a_live_film_runs_the_clock_to_each_watch_it_advances_to_then_holds_there():
    steps = [{"tool": "check_plan", "hour": 0}, {"tool": "advance", "hour": 24}, {"tool": "confirm_berths", "hour": 24},
             {"tool": "advance", "hour": 30}]
    frames = timeline({"steps": steps, "live": {}}, 70, **PACE)
    shown = [f.step for f in frames]
    assert shown == [0] * 10 + [0] * 10 + [1] * 12 + [1] * 10 + [2] * 10 + [3] * 3 + [3] * 10 + [3] * 20 + [3] * 20
    assert frames[20] == Frame(1, 2) and frames[31:42] == [Frame(1, 24)] * 11 and frames[54:65] == [Frame(3, 30)] * 11
    assert hours(frames) == sorted(hours(frames)) and frames[-1] == Frame(3, 70)


@pytest.mark.parametrize(("run", "model", "task_id"), LIVE)
def test_a_recorded_week_plays_forward_to_its_horizon(runs, run, model, task_id):
    rollout = runs.rollout(run, model, task_id)
    frames = timeline(rollout, 200)
    assert hours(frames) == sorted(hours(frames)) and frames[-1].hour == 200
    assert sorted({f.step for f in frames}) == list(range(len(rollout["steps"])))
    for k, step in enumerate(rollout["steps"]):
        assert max(f.hour for f in frames if f.step == k) == step["hour"] or k == len(rollout["steps"]) - 1


def test_the_command_lines():
    args = chrome_args("chrome", ROOT, 1280, 720)
    assert args[0] == "chrome" and args[-1] == "about:blank"
    assert {"--headless=new", "--remote-debugging-port=0", f"--user-data-dir={ROOT}", "--window-size=1280,720",
            "--hide-scrollbars", "--disable-smooth-scrolling", "--force-device-scale-factor=1"} <= set(args)
    args = ffmpeg_args("ffmpeg", ROOT / "out.mp4", 30, "a title")
    assert " ".join(args).startswith("ffmpeg -v error -y -f image2pipe -framerate 30 -c:v mjpeg -i - -c:v libx264")
    assert {"yuv420p", "scale=out_range=tv:out_color_matrix=bt709", "+faststart", "title=a title",
            f"comment={twin.ATTRIBUTION}"} <= set(args)
    assert args[-1] == str(ROOT / "out.mp4")
    args = gif_args("ffmpeg", ROOT / "a.mp4", ROOT / "a.gif")
    assert "palettegen" in args[args.index("-vf") + 1] and args[-3:] == ["-loop", "0", str(ROOT / "a.gif")]


@pytest.mark.browser
def test_a_one_second_take(monkeypatch, tmp_path):
    monkeypatch.setattr(record, "RUNS", ROOT)
    monkeypatch.setattr(record, "timeline", lambda rollout, horizon, **_: [Frame(0, 4 * i) for i in range(10)])
    out = tmp_path / "take.mp4"
    result = CliRunner().invoke(record.record_command, [
        "--sweep", "live-sonnet", "--model", SONNET, "--task", "dock-24B-w06x1-busy-0", "--out", str(out),
        "--size", "1280x720", "--fps", "10"])
    assert result.exit_code == 0, result.output
    probe = subprocess.run([shutil.which("ffprobe"), "-v", "error", "-count_frames", "-show_entries",
                            "stream=nb_read_frames,width,height,pix_fmt:format_tags=comment", "-of", "json", str(out)],
                           capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)
    [stream] = info["streams"]
    assert [stream[k] for k in ("width", "height", "nb_read_frames", "pix_fmt")] == [1280, 720, "10", "yuv420p"]
    assert info["format"]["tags"]["comment"] == twin.ATTRIBUTION


def test_a_page_that_never_answers_is_a_click_error(monkeypatch):
    class Silent:
        def send(self, message):
            pass

        def recv(self, timeout):
            raise TimeoutError

    monkeypatch.setattr(record, "ANSWER_SECONDS", 0.01)
    with pytest.raises(click.ClickException, match="Chrome did not answer Page.navigate"):
        Page(Silent()).call("Page.navigate", url="about:blank")


@pytest.mark.browser
def test_a_live_week_shows_no_news_before_its_bulletin(runs):
    run, model, task_id = LIVE[0]
    ro = runs.rollout(run, model, task_id)
    steps, bulletins = ro["steps"], ro["live"]["bulletins"]
    server = serve(runs, twin.ensure(), 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with record.recording(record.episode_url(server.server_port, run, model, task_id), record.find_chrome(None),
                              1280, 720) as (page, _):
            def at(k: int, hour: float) -> dict:
                page.js(f"portsim.show({k})")
                page.js(f"portsim.time({hour})")
                return page.js(SHOWN)

            def news(seen: dict, k: int) -> list[bool]:
                return [b["text"].split("\n")[0] in seen["transcript"] for b in bulletins if b["step"] == k]

            for k, step in enumerate(steps):
                week = step["task"] if k < len(steps) - 1 else runs.pack.public(runs.pack.get(task_id))
                seen = at(k, step["hour"])
                assert seen["task"] == week and seen["scene"]
                assert sorted(seen["afloat"]) == [s["id"] for s in week["ships"]]
                assert sorted(seen["drawn"]) == sorted(p["ship"] for p in step["plan"])
                assert (seen["winds"], seen["outages"]) == (len(week["rules"]["no_moves"]),
                                                            len(week["rules"]["crane_outages"]))
                assert all(news(seen, j) == [j <= k] * len(news(seen, j)) for j in range(len(steps)))
                assert bool(re.search(r"Watch \d+ of", seen["panel"])) == (k == len(steps) - 1)
                if step["tool"] == "advance" and k and step["hour"] > steps[k - 1]["hour"]:
                    flying = at(k, (steps[k - 1]["hour"] + step["hour"]) / 2)
                    assert flying["task"] == steps[k - 1]["task"] and f"Advancing to watch {step['watch']}…" in (
                        flying["panel"])
                    assert step["time"] not in flying["panel"] and not any(news(flying, k))
    finally:
        server.shutdown()
        server.server_close()
