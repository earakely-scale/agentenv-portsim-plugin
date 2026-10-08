"""Fetch the weather behind portsim-wind into a cache outside the repo: the readings of Meteocat's XEMA station Y7
(Bocana Sud), the anemometer the port ordinance names, and the ECMWF HRES forecasts as published; and build the
weather weeks from that cache.

`fetch` downloads, into --cache (default ~/.cache/agentenv-portsim/wind):

- y7/pass1/YYYY-MM.json: Y7's 30-minute mean wind (VV10, variable 30) and 3-second gust (VVx10, variable 50) at 10 m,
  with their validation state (codi_estat), every month from 2023-01 to 2026-01 (2025-W52's 264 hours end on
  2026-01-02), as the Generalitat's open-data portal returned them (dataset nzvn-apee, anonymous Socrata API; not the
  Meteocat API, whose terms forbid passing data on). YYYY-MM.meta.json pins the month: the sha256 of its canonical
  rows (each row as sorted-key compact JSON, the lines sorted and joined by newlines), the row count, the codi_estat
  counts and the portal's Last-Modified. `--y7-pass N` fetches the readings alone again into y7/passN, so two
  independent passes can be compared month by month.
- weeks.json: the candidate weather weeks, from pass 1: 2023-W04 to 2025-W52 weeks with a window of wind above 25 kn
  of 4 hours or more or any hour above 30 kn, unless that rests on one unvalidated gust reading, plus the bust weeks.
- ecmwf/<grid>/YYYYMMDDHH.json: per run of ECMWF HRES open data on AWS (CC BY 4.0), each step's 10u and 10v message:
  object key, byte offset and length (the HTTP Range bytes=offset-(offset+length-1) of the .grib2 object), sha256 of
  those bytes, the object's Last-Modified, and the value in m/s at the nearest sea cell. No GRIB is kept. The runs:
  every run (4 a day, steps 0-72 h) from the one serving hour 0 of a candidate week, the latest published (init + 9 h)
  by Monday 00:00 UTC, to the one serving its hour 263; the 00/12Z runs at steps 9-72 h over the calibration fits'
  periods (0.4 degree Feb 2024-Jan 2025, 0.25 degree Feb 2024-Dec 2025); and the 2023-Jan 2024 0.4 degree 00/12Z runs
  at the day-ahead steps 24-36 h that screen calm weeks for false alarms.

Every file is written atomically and a rerun fetches only what is missing. summary.json counts the work and the
failures; `done` is written when nothing is missing, else the command exits non-zero.

`build` reads only the cache (y7/pass1 and y7/pass2, whose digests must agree, weeks.json, ecmwf/) and writes, into
--out (default data/):

- wind/weather.jsonl: one line per week of weeks.json, which the storm rule must still give, in date order. The truth
  is the hours whose rule wind is above 25 kn (min_length 300) or 30 kn (min_length 0), merged across gaps of up to 2
  hours with each window's share of unvalidated readings, and as observed, unmerged. The runs are every run in force
  at an hour 0, 6, ..., 258 of the week: the latest with all 25 steps whose every message was out by init + 9 h. Each
  run's 3-hourly wind is calibrated to the anemometer in whole knots by quantile maps per lead block (0-23, 24-47,
  48-72 h), fitted on another year's 00/12Z runs on the same grid (2023 on 0.4 degree Feb 2024-Jan 2025, 2024 on
  0.25 degree 2025, 2025 on 0.25 degree Feb-Dec 2024); its windows are agentenv_portsim.wind.run_windows'.
- wind/weather-sources.json: the pins: every ECMWF message the weeks' runs use (key, range, sha256, Last-Modified)
  with ECMWF's attribution, each Y7 month's digest, and the calibration's description, which the wind pack's manifest
  copies, the messages by the file's sha256 and their count. Never a reading, a quantile map or GRIB.

    uv run --with eccodes==2.49.0 python scripts/wind_weather.py fetch [--cache DIR] [--y7-pass N]
    uv run --no-sync --frozen --with eccodes==2.49.0 python scripts/wind_weather.py build [--cache DIR] [--out DIR]
"""

import argparse
import hashlib
import http.client
import json
import math
import os
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

import eccodes

from agentenv_portsim import wind

SOCRATA = "https://analisi.transparenciacatalunya.cat/resource/nzvn-apee.json"
STATION = "Y7"
FIRST_MONTH, LAST_MONTH = (2023, 1), (2026, 1)
Y7_LIMIT = 50000
Y7_TIMEOUT = 300
Y7_WORKERS = 4
MS_TO_KN = 3600 / 1852
FACTORS = {"30": 1.045, "50": 0.83 / 1.25}
"""Annex III's central reading at Y7: the 10-minute mean is 1.045 x the 30-minute mean, and the rule's 1-minute maximum
above 1.25 x the threshold is 0.83 x the 3-second gust, so both compare with the threshold itself."""
STORM_HOURS = 4
FIRST_WEEK, LAST_WEEK = "2023-W04", "2025-W52"
BUST_WEEKS = ("2023-W44", "2025-W14")
HOURS = 264
HOUR, HALF = timedelta(hours=1), timedelta(minutes=30)
EPOCH = datetime(*FIRST_MONTH, 1, tzinfo=UTC)

BUCKET = "ecmwf-forecasts.s3.eu-central-1.amazonaws.com"
FIRST_RUN = datetime(2023, 1, 18, tzinfo=UTC)
SWITCH = datetime(2024, 2, 28, 6, tzinfo=UTC)
"""The bucket files runs from here under ifs/, and the weeks' forecasts switch from the 0.4 to the 0.25 degree grid."""
CELLS = {"0p4": (41.2, 2.0), "0p25": (41.25, 2.25)}
"""The nearest sea cells to Y7 (land fraction 0.05 and 0.03): interpolating mixes in land cells and reads 8-9 kn low."""
GRID_DIRS = {"0p4": "0p4-beta", "0p25": "0p25"}
PARAMS = ("10u", "10v")
WEEK_STEPS = tuple(range(0, 73, 3))
FIT_STEPS = tuple(range(9, 73, 3))
DAY_AHEAD_STEPS = tuple(range(24, 37, 3))
FIT_YEARS = {2023: ("0p4", datetime(2024, 2, 1, tzinfo=UTC), datetime(2025, 1, 31, 12, tzinfo=UTC)),
             2024: ("0p25", datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, 12, tzinfo=UTC)),
             2025: ("0p25", datetime(2024, 2, 1, tzinfo=UTC), datetime(2024, 12, 31, 12, tzinfo=UTC))}
"""Each weather year's quantile maps are fitted on another year's 00/12Z runs, on the grid its weeks use, so no week is
calibrated on its own wind."""
FITS = [(grid, min(a for g, a, _ in FIT_YEARS.values() if g == grid),
         max(b for g, _, b in FIT_YEARS.values() if g == grid))
        for grid in dict.fromkeys(g for g, *_ in FIT_YEARS.values())]
"""The fetch's fit periods, one per grid: the span of the years' fits on it."""
SCREEN = ("0p4", FIRST_RUN, datetime(2024, 1, 31, 12, tzinfo=UTC))
WORKERS = 16
ATTEMPTS = 12
BACKOFF_SECONDS, BACKOFF_CAP = 0.5, 60.0
TIMEOUT = 120
RETRY_STATUS = {429, 500, 502, 503, 504}
PROGRESS_EVERY = 500

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = ((0, 24), (24, 48), (48, 73))
PERCENTILES = range(1, 100)
IN_FORCE_HOURS = range(0, HOURS, 6)
XEMA = "https://analisi.transparenciacatalunya.cat/d/nzvn-apee"
OPEN_DATA = "https://www.ecmwf.int/en/forecasts/datasets/open-data"
TERMS = "https://apps.ecmwf.int/datasets/licences/general/"


def cache_dir() -> Path:
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "agentenv-portsim" / "wind"


def iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_atomic(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(body)
    os.replace(tmp, path)


def write_json(path: Path, data: object) -> None:
    write_atomic(path, (json.dumps(data, indent=1) + "\n").encode())


def backoff(attempt: int) -> None:
    time.sleep(random.uniform(0, min(BACKOFF_CAP, BACKOFF_SECONDS * 2 ** attempt)))


class Failure(Exception):
    pass


def months() -> list[str]:
    out, (y, m) = [], FIRST_MONTH
    while (y, m) <= LAST_MONTH:
        out.append(f"{y}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def y7_url(month: str) -> str:
    y, m = map(int, month.split("-"))
    end = f"{y + m // 12}-{m % 12 + 1:02d}"
    where = (f"codi_estacio='{STATION}' AND codi_variable in ('30','50') AND data_lectura >= '{month}-01T00:00:00' "
             f"AND data_lectura < '{end}-01T00:00:00'")
    query = {"$where": where, "$order": "data_lectura,codi_variable", "$limit": Y7_LIMIT}
    return f"{SOCRATA}?{urllib.parse.urlencode(query)}"


def digest(rows: list[dict]) -> str:
    lines = sorted(json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False) for r in rows)
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def fetch_month(directory: Path, month: str) -> dict:
    url = y7_url(month)
    for attempt in range(ATTEMPTS):
        try:
            with urllib.request.urlopen(url, timeout=Y7_TIMEOUT) as response:
                body, modified = response.read(), response.headers["Last-Modified"]
            rows = json.loads(body)
            break
        except urllib.error.HTTPError as error:
            if error.code not in RETRY_STATUS:
                raise Failure(f"Y7 {month}: HTTP {error.code}") from error
        except (OSError, http.client.HTTPException, ValueError):
            pass
        backoff(attempt)
    else:
        raise Failure(f"Y7 {month}: gave up after {ATTEMPTS} attempts")
    if len(rows) >= Y7_LIMIT:
        raise Failure(f"Y7 {month}: {len(rows)} rows reach the query limit")
    meta = {"month": month, "url": url, "fetched": iso(datetime.now(UTC)),
            "last_modified": iso(parsedate_to_datetime(modified)), "rows": len(rows), "sha256": digest(rows),
            "codi_estat": dict(sorted(Counter(r.get("codi_estat", "") for r in rows).items()))}
    write_atomic(directory / f"{month}.json", body)
    write_json(directory / f"{month}.meta.json", meta)
    return meta


def fetch_y7(directory: Path) -> tuple[dict, list[str]]:
    metas, failures = {}, []
    todo = [m for m in months() if not (directory / f"{m}.meta.json").is_file()]
    started = time.monotonic()
    with ThreadPoolExecutor(Y7_WORKERS) as pool:
        futures = {pool.submit(fetch_month, directory, m): m for m in todo}
        for future in as_completed(futures):
            month = futures[future]
            try:
                meta = future.result()
            except Failure as error:
                failures.append(str(error))
                print(error, flush=True)
                continue
            print(f"Y7 {directory.name} {month}: {meta['rows']} rows, codi_estat {meta['codi_estat']}, "
                  f"sha256 {meta['sha256'][:12]}, at {time.monotonic() - started:.0f} s", flush=True)
    for month in months():
        path = directory / f"{month}.meta.json"
        if path.is_file():
            metas[month] = json.loads(path.read_text())
    return metas, failures


def readings(directory: Path) -> dict[datetime, dict[str, tuple[float, bool]]]:
    """Each half-hour's mean and gust in knots, by variable, with whether Meteocat has validated the reading."""
    out: dict[datetime, dict[str, tuple[float, bool]]] = defaultdict(dict)
    for path in sorted(directory.glob("????-??.json")):
        for r in json.loads(path.read_bytes()):
            if r["codi_variable"] in FACTORS:
                t = datetime.fromisoformat(r["data_lectura"]).replace(tzinfo=UTC)
                out[t][r["codi_variable"]] = (float(r["valor_lectura"]) * MS_TO_KN, r.get("codi_estat") == "V")
    return out


def rule_wind(obs: dict, hour: datetime, skip: tuple[datetime, str] | None = None) -> float | None:
    """The hour's wind under Annex III's central reading: the largest of its half-hours' converted means and gusts."""
    xs = [FACTORS[v] * x for t in (hour, hour + HALF) for v, (x, _) in obs.get(t, {}).items() if (t, v) != skip]
    return max(xs) if xs else None


def hourly(obs: dict) -> dict[datetime, float | None]:
    return {h: rule_wind(obs, h) for h in sorted({t.replace(minute=0) for t in obs})}


def windows(hours: dict[datetime, float | None], kn: int) -> list[tuple[datetime, int]]:
    """The runs of hours whose rule wind is above kn, merged as the truth is, as (start, hours)."""
    above = [(h - EPOCH) // HOUR for h, x in hours.items() if x is not None and x > kn]
    return [(EPOCH + w["start"] * HOUR, w["end"] - w["start"]) for w in wind.merge(above, 0)]


def iso_week(t: datetime) -> str:
    year, week, _ = t.isocalendar()
    return f"{year}-W{week:02d}"


def storm_weeks(hours: dict[datetime, float | None]) -> set[str]:
    (_, low), (_, high) = wind.THRESHOLDS
    weeks = {iso_week(a) for a, length in windows(hours, low) if length >= STORM_HOURS}
    weeks |= {iso_week(a) for a, _ in windows(hours, high)}
    return {w for w in weeks if FIRST_WEEK <= w <= LAST_WEEK}


def candidate_weeks(obs: dict) -> dict:
    hours = hourly(obs)
    storms = storm_weeks(hours)
    dropped: dict[str, str] = {}
    for t, r in sorted(obs.items()):
        gust, valid = r.get("50", (0.0, True))
        if valid or FACTORS["50"] * gust <= min(kn for _, kn in wind.THRESHOLDS):
            continue
        h = t.replace(minute=0)
        for week in storms - storm_weeks(hours | {h: rule_wind(obs, h, (t, "50"))}):
            dropped.setdefault(week, f"rests on one unvalidated gust reading, {gust:.1f} kn at {iso(t)}")
    storm = sorted(storms - set(dropped))
    return {"storm": storm, "bust": list(BUST_WEEKS), "dropped": dropped,
            "weeks": {w: iso(monday(w)) for w in sorted(set(storm) | set(BUST_WEEKS))}}


def monday(week: str) -> datetime:
    year, number = week.split("-W")
    return datetime.fromisocalendar(int(year), int(number), 1).replace(tzinfo=UTC)


def every(start: datetime, end: datetime, hours: int) -> list[datetime]:
    return [start + timedelta(hours=h) for h in range(0, int((end - start) / HOUR) + 1, hours)]


def week_runs(week: str) -> list[datetime]:
    """The runs that can serve the week's hours 0-263, from the latest published (init + 9 h) by hour 0."""
    first, last = -wind.PUBLISHED_HOURS // 6 * 6, (HOURS - 1 - wind.PUBLISHED_HOURS) // 6 * 6
    return every(monday(week) + first * HOUR, monday(week) + last * HOUR, 6)


def week_grid(init: datetime) -> str:
    return "0p4" if init < SWITCH else "0p25"


def plan(weeks: Iterable[str]) -> dict[tuple[str, datetime], dict[int, str]]:
    """Every (grid, run) to fetch with its steps, each step under the first kind that needs it: the weeks' runs, then
    the fits', then the screen's."""
    out: dict[tuple[str, datetime], dict[int, str]] = {}

    def add(kind: str, grid: str, inits: list[datetime], steps: tuple[int, ...]) -> None:
        for init in inits:
            for step in steps:
                out.setdefault((grid, init), {}).setdefault(step, kind)

    for week in weeks:
        for init in week_runs(week):
            add("week", week_grid(init), [init], WEEK_STEPS)
    for grid, start, end in FITS:
        add("fit", grid, every(start, end, 12), FIT_STEPS)
    grid, start, end = SCREEN
    add("screen", grid, every(start, end, 12), DAY_AHEAD_STEPS)
    return out


def key(grid: str, init: datetime, step: int) -> str:
    stream = "oper" if init.hour in (0, 12) else "scda"
    day, hh = f"{init:%Y%m%d}", f"{init:%H}"
    ifs = "ifs/" if init >= SWITCH else ""
    return f"{day}/{hh}z/{ifs}{GRID_DIRS[grid]}/{stream}/{day}{hh}0000-{step}h-{stream}-fc"


def run_path(cache: Path, grid: str, init: datetime) -> Path:
    return cache / "ecmwf" / grid / f"{init:%Y%m%d%H}.json"


class Stats:
    def __init__(self, todo: int) -> None:
        self.lock = threading.Lock()
        self.todo, self.started = todo, time.monotonic()
        self.counts: Counter = Counter()

    def add(self, **counts: int) -> None:
        with self.lock:
            before = self.counts["messages"] // PROGRESS_EVERY
            self.counts.update(counts)
            if self.counts["messages"] // PROGRESS_EVERY > before:
                c, elapsed = self.counts, time.monotonic() - self.started
                print(f"ECMWF {c['messages']}/{self.todo} messages, {c['bytes'] / 1e9:.2f} GB, {elapsed:.0f} s, "
                      f"{c['messages'] / elapsed:.1f} messages/s, {c['requests']} requests, {c['slowdowns']} SlowDown, "
                      f"{c['retries']} retries, {c['absent']} absent, {c['failed']} failed", flush=True)


class Bucket:
    """One keep-alive HTTPS connection per thread, retrying throttling and transient errors with exponential backoff
    and full jitter."""

    def __init__(self, stats: Stats) -> None:
        self.stats, self.local = stats, threading.local()

    def get(self, path: str, offset: int | None = None, length: int | None = None) -> tuple[bytes, datetime] | None:
        headers = {} if offset is None else {"Range": f"bytes={offset}-{offset + length - 1}"}
        for attempt in range(ATTEMPTS):
            if getattr(self.local, "conn", None) is None:
                self.local.conn = http.client.HTTPSConnection(BUCKET, timeout=TIMEOUT)
            try:
                self.local.conn.request("GET", path, headers=headers)
                response = self.local.conn.getresponse()
                body = response.read()
            except (OSError, http.client.HTTPException):
                self.local.conn.close()
                self.local.conn = None
                self.stats.add(retries=1)
                backoff(attempt)
                continue
            self.stats.add(requests=1, bytes=len(body))
            if response.status == 404:
                return None
            if response.status == (200 if offset is None else 206) and len(body) == (length or len(body)):
                return body, parsedate_to_datetime(response.getheader("Last-Modified"))
            if response.status in (200, 206) or response.status in RETRY_STATUS:
                self.stats.add(retries=1, slowdowns=int(response.status == 503))
                backoff(attempt)
                continue
            raise Failure(f"{path.rsplit('.', 1)[1]}: HTTP {response.status}")
        raise Failure(f"{path.rsplit('.', 1)[1]}: gave up after {ATTEMPTS} attempts")


def point(message: bytes, grid: str, init: datetime, step: int, param: str) -> float:
    gid = eccodes.codes_new_from_message(message)
    try:
        got = tuple(eccodes.codes_get(gid, k) for k in ("shortName", "dataDate", "dataTime", "endStep"))
        if got != (param, int(f"{init:%Y%m%d}"), init.hour * 100, step):
            raise Failure(f"{param}: the message is {got}")
        lat, lon = CELLS[grid]
        near = eccodes.codes_grib_find_nearest(gid, lat, lon)[0]
        if abs(near.lat - lat) > 1e-6 or abs((near.lon - lon + 180) % 360 - 180) > 1e-6:
            raise Failure(f"{param}: nearest grid point {near.lat}, {near.lon}")
        return float(near.value)
    finally:
        eccodes.codes_release(gid)


def fetch_step(bucket: Bucket, grid: str, init: datetime, step: int) -> dict | None:
    """The step's two messages: None if the archive lacks the step or its GRIB file, a param None if the step lacks
    it."""
    k = key(grid, init, step)
    index = bucket.get(f"/{k}.index")
    if index is None:
        return None
    found = {}
    for line in index[0].decode().splitlines():
        m = json.loads(line)
        if m.get("levtype") == "sfc" and m.get("param") in PARAMS:
            found[m["param"]] = (m["_offset"], m["_length"])
    out: dict[str, dict | None] = {}
    for param in PARAMS:
        if param not in found:
            out[param] = None
            continue
        offset, length = found[param]
        got = bucket.get(f"/{k}.grib2", offset, length)
        if got is None:
            return None
        body, modified = got
        out[param] = {"key": f"{k}.grib2", "offset": offset, "length": length,
                      "sha256": hashlib.sha256(body).hexdigest(), "last_modified": iso(modified),
                      "value": point(body, grid, init, step, param)}
    return out


def load_run(cache: Path, grid: str, init: datetime) -> dict:
    path = run_path(cache, grid, init)
    if path.is_file():
        return json.loads(path.read_text())
    return {"grid": grid, "init": iso(init), "cell": list(CELLS[grid]), "steps": {}}


def tally(cache: Path, work: dict[tuple[str, datetime], dict[int, str]]) -> tuple[dict[str, Counter], list[str]]:
    """The planned messages by kind and grid as the cache holds them: present, absent from the archive, or missing."""
    kinds: dict[str, Counter] = defaultdict(Counter)
    absent = []
    for (grid, init), steps in work.items():
        have = load_run(cache, grid, init)["steps"]
        for kind in dict.fromkeys(steps.values()):
            kinds[f"{kind} {grid}"]["runs"] += 1
        for step, kind in steps.items():
            c = kinds[f"{kind} {grid}"]
            c["messages"] += len(PARAMS)
            if str(step) not in have:
                c["missing"] += len(PARAMS)
                continue
            got = have[str(step)]
            gone = list(PARAMS) if got is None else [p for p, v in got.items() if v is None]
            c["absent"] += len(gone)
            c["present"] += len(PARAMS) - len(gone)
            absent += [f"{key(grid, init, step)} {p}" for p in gone]
    return kinds, absent


def fetch_ecmwf(cache: Path, weeks: list[str]) -> dict:
    work = plan(weeks)
    runs = {run: load_run(cache, *run) for run in work}
    todo = [(grid, init, step) for (grid, init), steps in work.items() for step in steps
            if str(step) not in runs[grid, init]["steps"]]
    kinds, _ = tally(cache, work)
    stats = Stats(len(PARAMS) * len(todo))
    print(f"ECMWF plan: {sum(c['messages'] for c in kinds.values())} messages from {len(work)} runs, {stats.todo} "
          "to fetch; " + "; ".join(f"{k} {dict(c)}" for k, c in kinds.items()), flush=True)
    bucket = Bucket(stats)
    failures: list[str] = []
    with ThreadPoolExecutor(WORKERS) as pool:
        futures = {pool.submit(fetch_step, bucket, *job): job for job in todo}
        try:
            for future in as_completed(futures):
                grid, init, step = futures[future]
                try:
                    got = future.result()
                except (Failure, eccodes.CodesInternalError) as error:
                    failures.append(f"{key(grid, init, step)} {error}")
                    stats.add(messages=len(PARAMS), failed=len(PARAMS))
                    continue
                run = runs[grid, init]
                run["steps"] = dict(sorted((run["steps"] | {str(step): got}).items(), key=lambda s: int(s[0])))
                write_json(run_path(cache, grid, init), run)
                stats.add(messages=len(PARAMS),
                          absent=len(PARAMS) if got is None else sum(v is None for v in got.values()))
        except BaseException:
            pool.shutdown(wait=False, cancel_futures=True)
            raise
    kinds, absent = tally(cache, work)
    c = stats.counts
    return {"runs": len(work), "kinds": {k: dict(v) for k, v in kinds.items()},
            "messages": sum(v["messages"] for v in kinds.values()),
            "missing": sum(v["missing"] for v in kinds.values()), "fetched": c["messages"] - c["failed"],
            "bytes": c["bytes"], "requests": c["requests"], "retries": c["retries"], "slowdowns": c["slowdowns"],
            "seconds": round(time.monotonic() - stats.started, 1), "absent": absent, "failures": failures}


def fetch(cache: Path, y7_pass: int) -> int:
    started, began = time.monotonic(), iso(datetime.now(UTC))
    directory = cache / "y7" / f"pass{y7_pass}"
    out = cache if y7_pass == 1 else directory
    (out / "done").unlink(missing_ok=True)
    metas, y7_failures = fetch_y7(directory)
    summary: dict = {"started": began, "y7": {"pass": y7_pass, "months": len(metas),
                                               "rows": sum(m["rows"] for m in metas.values()),
                                               "failures": y7_failures}}
    complete = not y7_failures
    if y7_pass > 1:
        first = {m: cache / "y7" / "pass1" / f"{m}.meta.json" for m in metas}
        summary["y7"]["differs_from_pass1"] = [m for m, meta in metas.items() if first[m].is_file()
                                               and json.loads(first[m].read_text())["sha256"] != meta["sha256"]]
    elif complete:
        weeks = candidate_weeks(readings(directory))
        write_json(cache / "weeks.json", weeks)
        print(f"Weeks: storm {weeks['storm']}, bust {weeks['bust']}, dropped {weeks['dropped']}", flush=True)
        summary["weeks"] = weeks
        summary["ecmwf"] = fetch_ecmwf(cache, list(weeks["weeks"]))
        complete = summary["ecmwf"]["missing"] == 0
    summary |= {"finished": iso(datetime.now(UTC)), "seconds": round(time.monotonic() - started, 1),
                "complete": complete}
    write_json(out / "summary.json", summary)
    print(f"Wrote {out / 'summary.json'}: " + ("complete" if complete else "INCOMPLETE, rerun to resume"))
    if not complete:
        return 1
    write_atomic(out / "done", (summary["finished"] + "\n").encode())
    return 0


def speed(step: dict) -> float:
    return math.hypot(step["10u"]["value"], step["10v"]["value"]) * MS_TO_KN


def complete(run: dict, steps: Iterable[int]) -> bool:
    return all(run["steps"].get(str(s)) and all(run["steps"][str(s)].get(p) for p in PARAMS) for s in steps)


def usable(run: dict, init: datetime) -> bool:
    """Every step of the run is in the archive, and every message was out by init + 9 h."""
    return complete(run, WEEK_STEPS) and all(
        datetime.fromisoformat(m["last_modified"]) <= init + wind.PUBLISHED_HOURS * HOUR
        for s in WEEK_STEPS for m in run["steps"][str(s)].values())


def observed(obs: dict, hour: datetime) -> float | None:
    """The hour's rule wind, None without a mean reading."""
    return rule_wind(obs, hour) if any("30" in obs.get(t, {}) for t in (hour, hour + HALF)) else None


def block(lead: int) -> int:
    return next(i for i, (a, b) in enumerate(BLOCKS) if a <= lead < b)


def percentiles(xs: list[float]) -> list[float]:
    """numpy's default (linear) percentiles 1 to 99."""
    xs = sorted(xs)
    out = []
    for p in PERCENTILES:
        i, rest = divmod((len(xs) - 1) * p, 100)
        out.append(xs[i] + (xs[min(i + 1, len(xs) - 1)] - xs[i]) * rest / 100)
    return out


class QuantileMap:
    """A forecast's wind to the anemometer's, in whole knots: linear between the fit's percentiles (a tie in the
    forecast's taking the mean of the observed), proportional below the first and offset above the last."""

    def __init__(self, forecasts: list[float], observations: list[float]) -> None:
        self.f, self.o = percentiles(forecasts), percentiles(observations)
        tied: dict[float, list[float]] = defaultdict(list)
        for f, o in zip(self.f, self.o, strict=True):
            tied[f].append(o)
        self.knots = [(f, sum(os) / len(os)) for f, os in tied.items()]

    def __call__(self, x: float) -> int:
        if x < self.f[0]:
            v = self.o[0] * x / self.f[0] if self.f[0] else 0.0
        elif x > self.f[-1]:
            v = self.o[-1] + x - self.f[-1]
        else:
            i = max(i for i, (f, _) in enumerate(self.knots) if f <= x)
            (f0, o0), (f1, o1) = self.knots[i], self.knots[min(i + 1, len(self.knots) - 1)]
            v = o0 if f1 == f0 else o0 + (o1 - o0) * (x - f0) / (f1 - f0)
        return max(0, math.floor(v + 0.5))


def fit(cache: Path, obs: dict, grid: str, first: datetime, last: datetime) -> tuple[list[QuantileMap], dict]:
    """One map per lead block from the period's 00/12Z runs with every step 9-72 h, each step against the rule wind
    that blew in the hour it is valid for."""
    pairs: list[tuple[list[float], list[float]]] = [([], []) for _ in BLOCKS]
    runs = 0
    for init in every(first, last, 12):
        run = load_run(cache, grid, init)
        if not complete(run, FIT_STEPS):
            continue
        runs += 1
        for step in FIT_STEPS:
            if (o := observed(obs, init + step * HOUR)) is not None:
                pairs[block(step)][0].append(speed(run["steps"][str(step)]))
                pairs[block(step)][1].append(o)
    return [QuantileMap(f, o) for f, o in pairs], {"grid": grid, "period": [f"{first:%Y-%m-%d}", f"{last:%Y-%m-%d}"],
                                                   "fitted_runs": runs, "pairs": [len(f) for f, _ in pairs]}


def unvalidated(obs: dict, t0: datetime, window: dict) -> float:
    """The share of the window's readings, both variables in both half-hours of each hour, not validated."""
    valid = [v for h in range(window["start"], window["end"]) for t in (t0 + h * HOUR, t0 + h * HOUR + HALF)
             for _, v in obs.get(t, {}).values()]
    return round(valid.count(False) / len(valid), 3)


def check(record: dict) -> None:
    for r in record["runs"]:
        assert r["issued"] == r["init"] + wind.PUBLISHED_HOURS and r["init"] % 6 == 0, r
        assert len(r["kn"]) == len(WEEK_STEPS) and all(isinstance(x, int) and x >= 0 for x in r["kn"]), r
        assert r["windows"] == wind.run_windows(r["init"], r["kn"]), r


def week(index: int, name: str, kind: str, obs: dict, hours: dict, cache: Path, maps: list[QuantileMap]) -> dict:
    """The weather week's truth, the hours above each threshold merged and as observed, and every run in force at a
    6-hourly hour, the latest usable run (every step, every message out by init + 9 h) issued by then, in calibrated
    whole knots."""
    t0 = monday(name)
    flagged = {m: [h for h in range(HOURS) if (x := hours.get(t0 + h * HOUR)) is not None and x > kn]
               for m, kn in wind.THRESHOLDS}
    good = [init for init in week_runs(name) if usable(load_run(cache, week_grid(init), init), init)]
    in_force = [[i for i in good if i + wind.PUBLISHED_HOURS * HOUR <= t0 + h * HOUR] for h in IN_FORCE_HOURS]
    assert all(in_force), f"{name}: no run in force at some hour"
    runs = []
    for init in sorted({max(inits) for inits in in_force}):
        assert week_grid(init) == FIT_YEARS[int(name[:4])][0], (name, init)
        run, h = load_run(cache, week_grid(init), init), (init - t0) // HOUR
        kn = [maps[block(step)](speed(run["steps"][str(step)])) for step in WEEK_STEPS]
        runs.append({"run": iso(init), "init": h, "issued": h + wind.PUBLISHED_HOURS, "kn": kn,
                     "windows": wind.run_windows(h, kn)})
    record = {"id": f"e{index:02d}", "iso_week": name, "monday": iso(t0), "kind": kind,
              "windows": [w | {"unvalidated": unvalidated(obs, t0, w)}
                          for m, _ in wind.THRESHOLDS for w in wind.merge(flagged[m], m)],
              "observed": [w for m, _ in wind.THRESHOLDS for w in wind.merge(flagged[m], m, gap=0)], "runs": runs}
    check(record)
    return record


def ecmwf_sources(cache: Path, records: list[dict]) -> dict:
    used = {datetime.fromisoformat(r["run"]) for w in records for r in w["runs"]}
    messages = sorted((m["key"], m["offset"], m["length"], m["sha256"], m["last_modified"])
                      for init in used for s in WEEK_STEPS
                      for m in load_run(cache, week_grid(init), init)["steps"][str(s)].values())
    return {
        "data": "ECMWF IFS HRES open data (oper and scda streams), 10 m wind",
        "bucket": f"s3://{BUCKET.split('.')[0]}", "url": f"https://{BUCKET}",
        "registry": "https://registry.opendata.aws/ecmwf-forecasts/", "open_data": OPEN_DATA, "terms": TERMS,
        "copyright": f"© {min(used).year}-{max(used).year} European Centre for Medium-Range Weather Forecasts (ECMWF)",
        "acknowledgement": ("This data is based on data and products of the European Centre for Medium-Range Weather "
                            "Forecasts (ECMWF)."),
        "source": "www.ecmwf.int",
        "licence": ("This data is published under a Creative Commons Attribution 4.0 International (CC BY 4.0). "
                    "https://creativecommons.org/licenses/by/4.0/"),
        "disclaimer": ("ECMWF does not accept any liability whatsoever for any error or omission in the data, their "
                       "availability, or for any loss or damage arising from their use."),
        "modified": ("Modified: each run's 10 m wind at one grid point, every 3 hours to 72 hours, mapped to the Y7 "
                     "anemometer by quantiles and rounded to whole knots."),
        "cells": {g: list(c) for g, c in CELLS.items()},
        "grids": f"0p4 for runs before {iso(SWITCH)}, 0p25 from then",
        "speed": "hypot(10u, 10v) m/s x 3600/1852 kn at the cell",
        "publication_hours": wind.PUBLISHED_HOURS, "steps": list(WEEK_STEPS), "params": list(PARAMS),
        "range": "bytes=offset-(offset+length-1) of the key; sha256 of those bytes",
        "fields": ["key", "offset", "length", "sha256", "last_modified"], "messages": messages}


def y7_sources(cache: Path) -> dict:
    metas = [json.loads(p.read_text()) for p in sorted((cache / "y7" / "pass1").glob("*.meta.json"))]
    again = {p.name: json.loads(p.read_text())["sha256"] for p in (cache / "y7" / "pass2").glob("*.meta.json")}
    assert again == {f"{m['month']}.meta.json": m["sha256"] for m in metas}, "Y7 pass 2 differs from pass 1"
    return {
        "dataset": "nzvn-apee", "url": XEMA, "api": SOCRATA,
        "publisher": "Servei Meteorològic de Catalunya (Meteocat), via the Generalitat de Catalunya's open data portal",
        "station": "Y7", "name": "Barcelona – Bocana Sud",
        "variables": {"30": "VV10, wind speed at 10 m, 30-minute mean, m/s",
                      "50": "VVx10, wind gust at 10 m, 3-second maximum, m/s"},
        "conversion": {"knots": "m/s x 3600/1852", "30": FACTORS["30"], "50": round(FACTORS["50"], 3),
                       "rule": ("an hour is above T kn when either half-hour has 1.045 x the mean or 0.664 x the gust "
                                "above T; T = 25 (min_length 300) or 30 (min_length 0)")},
        "extracted": max(m["fetched"] for m in metas)[:10],
        "digest": ("sha256 of the month's rows as returned, each row as JSON with sorted keys, separators (',', ':') "
                   "and non-ASCII kept, the lines sorted and joined by newlines, UTF-8; codi_estat as the portal "
                   "returns it, absent from rows it has not yet given a state"),
        "pass2_identical": True,
        "months": [{"month": m["month"], "rows": m["rows"], "sha256": m["sha256"]} for m in metas]}


def calibration_sources(fits: dict[int, dict]) -> dict:
    return {
        "method": ("quantile mapping per lead block: the forecast's speed at the cell against the rule wind observed "
                   "at Y7 in the hour each step is valid for (the larger of 1.045 x the mean and 0.664 x the gust over "
                   "its half-hours, readings as published, pairs without a mean skipped)"),
        "percentiles": "p = 1 to 99 of the fit's forecasts and of its observations, linear between order statistics",
        "apply": ("linear between the percentiles, the mean observed where forecast percentiles tie; below the first, "
                  "proportional to it; above the last, offset from it; rounded half up to a whole knot, never below 0"),
        "blocks": [list(b) for b in BLOCKS], "fit_runs": "00 and 12 UTC runs with every step 9-72 h",
        "years": {str(year): f for year, f in fits.items()},
        "maps": "not published; approximately recoverable from the published whole knots and the pinned forecasts"}


def sources_text(sources: dict) -> str:
    rows = sources["ecmwf"]["messages"]
    text = json.dumps(sources | {"ecmwf": sources["ecmwf"] | {"messages": None}}, indent=1, ensure_ascii=False)
    body = ",\n".join("  " + json.dumps(list(r), separators=(",", ":")) for r in rows)
    return text.replace('"messages": null', '"messages": [\n' + body + "\n ]", 1) + "\n"


def build(cache: Path, out: Path) -> None:
    assert (cache / "done").is_file(), f"{cache}: the fetch is not complete"
    obs = readings(cache / "y7" / "pass1")
    hours = hourly(obs)
    weeks = json.loads((cache / "weeks.json").read_text())
    assert candidate_weeks(obs) == weeks, "the storm rule no longer gives weeks.json"
    fits = {year: fit(cache, obs, *spec) for year, spec in FIT_YEARS.items()}
    kinds = {w: "storm" for w in weeks["storm"]} | {w: "bust" for w in weeks["bust"]}
    records = [week(i, name, kinds[name], obs, hours, cache, fits[int(name[:4])][0])
               for i, name in enumerate(sorted(kinds))]
    sources = {"ecmwf": ecmwf_sources(cache, records), "y7": y7_sources(cache),
               "calibration": calibration_sources({year: f for year, (_, f) in fits.items()})}
    directory = out / "wind"
    write_atomic(directory / "weather.jsonl", "".join(
        json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in records).encode())
    write_atomic(directory / "weather-sources.json", sources_text(sources).encode())
    print(f"Wrote {directory}: {len(records)} weeks, {sum(len(r['runs']) for r in records)} runs, "
          f"{len(sources['ecmwf']['messages'])} messages")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    fetch_parser = commands.add_parser("fetch", help="download Y7 and the ECMWF messages into the cache")
    fetch_parser.add_argument("--cache", type=Path, default=cache_dir())
    fetch_parser.add_argument("--y7-pass", type=int, default=1,
                              help="fetch only Y7, again, into y7/passN (default 1: Y7, then the ECMWF runs)")
    build_parser = commands.add_parser("build", help="write <out>/wind/weather.jsonl and weather-sources.json")
    build_parser.add_argument("--cache", type=Path, default=cache_dir())
    build_parser.add_argument("--out", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    if args.command == "fetch":
        raise SystemExit(fetch(args.cache, args.y7_pass))
    build(args.cache, args.out)


if __name__ == "__main__":
    main()
