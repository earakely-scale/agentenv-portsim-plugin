"""Fetch the weather behind portsim-wind into a cache outside the repo: the readings of Meteocat's XEMA station Y7
(Bocana Sud), the anemometer the port ordinance names, and the ECMWF HRES forecasts as published.

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

    uv run --with eccodes==2.49.0 python scripts/wind_weather.py fetch [--cache DIR] [--y7-pass N]
"""

import argparse
import hashlib
import http.client
import json
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
THRESHOLDS = (25, 30)
MERGE_GAP = 2
STORM_HOURS = 4
FIRST_WEEK, LAST_WEEK = "2023-W04", "2025-W52"
BUST_WEEKS = ("2023-W44", "2025-W14")
HOURS = 264
PUBLISHED_HOURS = 9
HOUR, HALF = timedelta(hours=1), timedelta(minutes=30)

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
FITS = [("0p4", datetime(2024, 2, 1, tzinfo=UTC), datetime(2025, 1, 31, 12, tzinfo=UTC)),
        ("0p25", datetime(2024, 2, 1, tzinfo=UTC), datetime(2025, 12, 31, 12, tzinfo=UTC))]
SCREEN = ("0p4", FIRST_RUN, datetime(2024, 1, 31, 12, tzinfo=UTC))
WORKERS = 16
ATTEMPTS = 12
BACKOFF_SECONDS, BACKOFF_CAP = 0.5, 60.0
TIMEOUT = 120
RETRY_STATUS = {429, 500, 502, 503, 504}
PROGRESS_EVERY = 500


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


def windows(hours: Iterable[datetime]) -> list[tuple[datetime, datetime]]:
    """Runs of the hours as [start, end), merged across gaps of up to MERGE_GAP hours."""
    out: list[list[datetime]] = []
    for h in sorted(hours):
        if out and h <= out[-1][1] + MERGE_GAP * HOUR:
            out[-1][1] = h + HOUR
        else:
            out.append([h, h + HOUR])
    return [(a, b) for a, b in out]


def iso_week(t: datetime) -> str:
    year, week, _ = t.isocalendar()
    return f"{year}-W{week:02d}"


def storm_weeks(hours: dict[datetime, float | None]) -> set[str]:
    above = {t: [h for h, x in hours.items() if x is not None and x > t] for t in THRESHOLDS}
    weeks = {iso_week(a) for a, b in windows(above[25]) if b - a >= STORM_HOURS * HOUR}
    weeks |= {iso_week(a) for a, _ in windows(above[30])}
    return {w for w in weeks if FIRST_WEEK <= w <= LAST_WEEK}


def candidate_weeks(obs: dict) -> dict:
    hours = hourly(obs)
    storms = storm_weeks(hours)
    dropped: dict[str, str] = {}
    for t, r in sorted(obs.items()):
        gust, valid = r.get("50", (0.0, True))
        if valid or FACTORS["50"] * gust <= min(THRESHOLDS):
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


def plan(weeks: Iterable[str]) -> dict[tuple[str, datetime], dict[int, str]]:
    """Every (grid, run) to fetch with its steps, each step under the first kind that needs it: the weeks' runs, then
    the fits', then the screen's."""
    out: dict[tuple[str, datetime], dict[int, str]] = {}

    def add(kind: str, grid: str, inits: list[datetime], steps: tuple[int, ...]) -> None:
        for init in inits:
            for step in steps:
                out.setdefault((grid, init), {}).setdefault(step, kind)

    first, last = -PUBLISHED_HOURS // 6 * 6, (HOURS - 1 - PUBLISHED_HOURS) // 6 * 6
    for week in weeks:
        for init in every(monday(week) + first * HOUR, monday(week) + last * HOUR, 6):
            add("week", "0p4" if init < SWITCH else "0p25", [init], WEEK_STEPS)
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
    """The step's two messages, None if the archive lacks the step, a param None if the step lacks it."""
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
            raise Failure(f"{param}: HTTP 404 for a message the index lists")
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    fetch_parser = commands.add_parser("fetch", help="download Y7 and the ECMWF messages into the cache")
    fetch_parser.add_argument("--cache", type=Path, default=cache_dir())
    fetch_parser.add_argument("--y7-pass", type=int, default=1,
                              help="fetch only Y7, again, into y7/passN (default 1: Y7, then the ECMWF runs)")
    args = parser.parse_args()
    if args.command == "fetch":
        raise SystemExit(fetch(args.cache, args.y7_pass))


if __name__ == "__main__":
    main()
