// A live week's rollout: the transcript by watch with the bulletins as they arrived, a watch panel on the virtual
// clock, and the dock chart marked with the freeze line and each window's status. Up to the last step, the chart, the
// 3D quay, the panel and the transcript show only what the planner knew; the last step plays out the real week.
// The transcript loop is adapted from PortSimEnv's transcript.js (FineEnvs b0f4c2f, Apache-2.0).
import { BerthChart } from "../chart.js";
import { clockAt, escapeHtml, evaluatePlan, fmtNum } from "../model.js";
import { checkSummary, planTable } from "../transcript.js?v=upstream";
import { currentStage } from "./stage.js";

const STATUSES = ["departed", "berthed", "frozen", "open", "draft"];
const SVG = "http://www.w3.org/2000/svg";
const INFEASIBLE = '<i class="dot bad"></i>infeasible';
const WIND_CREDIT = "Forecast: ECMWF open data, CC BY 4.0, modified · Observed: Meteocat XEMA Y7, derived windows";

const shipName = (task, id) => (task.ships.find((s) => s.id === Number(id)) || {}).name || `ship ${id}`;
const names = (task, ids) => ids.map((id) => escapeHtml(shipName(task, id))).join(", ") || "none";
const firstLine = (s, n = 80) => {
  const line = String(s || "").trim().split("\n")[0];
  return line.length > n ? `${line.slice(0, n - 1)}…` : line;
};
const parsed = (s) => {
  try {
    return JSON.parse(s);
  } catch {
    return null;
  }
};
const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;

/** News that arrives with an advance's watch: known from step k once the clock reaches that watch. */
function arriving(html, k) {
  const d = document.createElement("div");
  d.innerHTML = html;
  Object.assign(d.dataset, { known: k, arrive: "" });
  return d;
}

function virtualTime(task, t) {
  return new Date(Date.parse(task.week_start_utc) + Math.round(t * 60) * 60e3).toISOString().replace(".000Z", "Z");
}

/** Each ship's window status at hour t: fixed windows berth and sail as t passes, and after the last step every
 * window is fixed; entries not confirmed are drafts. */
function statuses(step, t) {
  const out = new Map();
  const confirmed = new Map(step.windows.map((w) => [w.ship, w]));
  for (const w of step.windows) out.set(w.ship, w.status === "open" && !step.last ? "open" : w.departure <= t ? "departed" : w.berth_hour <= t ? "berthed" : "frozen");
  for (const p of step.plan) {
    const w = confirmed.get(p.ship);
    if (!w || w.berth_hour !== p.berth_hour || w.section !== p.section || w.cranes !== p.cranes) out.set(p.ship, "draft");
  }
  return out;
}

function mark(chart, step, t) {
  const st = statuses(step, t);
  for (const [id, g] of chart.shipEls || []) for (const s of STATUSES) g.classList.toggle(`ps-${s}`, st.get(id) === s);
}

function overlay(chart, step, t) {
  if (!chart.geom) return;
  for (const e of chart.svg.querySelectorAll(".ps-ov")) e.remove();
  mark(chart, step, t);
  if (step.frozen_before <= step.hour) return;
  const { x, top, bottom } = chart.geom;
  const [under, over] = [0, 1].map(() => document.createElementNS(SVG, "g"));
  for (const g of [under, over]) g.setAttribute("class", "ps-ov");
  const add = (g, tag, attrs) => {
    const e = document.createElementNS(SVG, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    return g.appendChild(e);
  };
  add(under, "rect", { class: "ps-frozen-zone", x: x(step.hour), y: top, width: Math.max(1, x(step.frozen_before) - x(step.hour)), height: bottom - top });
  add(under, "line", { class: "ps-freeze", x1: x(step.frozen_before), x2: x(step.frozen_before), y1: top, y2: bottom });
  if (!chart.mini) add(over, "text", { class: "ax ps-freeze-t", x: x(step.frozen_before) + 3, y: bottom - 3 }).textContent = `freeze line h ${step.frozen_before}`;
  chart.svg.insertBefore(under, chart.svg.querySelector("g.ships"));
  chart.svg.appendChild(over);
}

/** Keep the overlay through the chart's own re-renders (setData, resize). */
function keepOverlay(chart, current) {
  const render = chart.render.bind(chart);
  chart.render = () => {
    render();
    const [step, t] = current();
    if (step) overlay(chart, step, t);
  };
}

function knownHtml(kn) {
  return kn.feasible
    ? `<i class="dot ok"></i>As known: feasible · cost ${kn.cost}${kn.excused_cost ? ` (excused ${kn.excused_cost})` : ""}`
    : `<i class="dot bad"></i>As known: infeasible · ${plural(kn.problems, "problem")}`;
}

/** The plan's pilots and tugs at hour t against those free for our ships, and the cuts in force. */
function marineHtml(m, t) {
  const h = Math.floor(t);
  const [, pilots, tugs] = m.ours.find(([hour]) => hour === h) || [h, 0, 0];
  const free = (pool) => (h < m.hours ? m[pool].free[h] : m[pool].pool);
  const parts = [`h${h}`, `pilots: ours ${pilots}, free ${free("pilots")}`, `tugs: ours ${tugs}, free ${free("tugs")}`];
  if (pilots > free("pilots") || tugs > free("tugs")) parts.push('<b class="ps-short">short</b>');
  for (const c of m.cuts) if (c.start <= h && h < c.end) parts.push(`${escapeHtml(c.from)}: ${c.count} out h${c.start}–${c.end}`);
  return `<div class="ps-line ps-marine">${parts.map((x) => `<span>${x}</span>`).join(" · ")}</div>`;
}

const spans = (ws) => ws.map((w) => `${w.start}–${w.end}`).join(", ") || "none";
const long = (ws) => ws.filter((w) => w.min_length > 0);

/** The forecast in force at the watch shown, and under it a strip over hours [0, horizon) and 0–40 kn: the forecast's
 * knots and windows, the 25 and 30 kn lines, and the windows of the wind that blew (``blew``) up to hour t. */
function windHtml(wind, t, blew, horizon) {
  const [W, top, base, track] = [440, 1, 31, 37];
  const r = (v) => Math.round(v * 10) / 10;
  const x = (h) => r((Math.max(0, Math.min(h, horizon)) / horizon) * W);
  const y = (kn) => r(base - (Math.min(kn, 40) / 40) * (base - top));
  const rect = (cls, a, b, y0, y1) => `<rect class="${cls}" x="${x(a)}" y="${y0}" width="${r(x(b) - x(a))}" height="${y1 - y0}"/>`;
  const level = (w) => (w.min_length > 0 ? 25 : 30);
  const days = Array.from({ length: Math.ceil(horizon / 24) - 1 }, (_, d) => x((d + 1) * 24));
  const nodes = wind.kn.filter(([h]) => h <= horizon);
  const [last, past] = [nodes[nodes.length - 1], wind.kn.find(([h]) => h > horizon)];
  if (last && past) nodes.push([horizon, last[1] + ((past[1] - last[1]) * (horizon - last[0])) / (past[0] - last[0])]);
  const strip = [
    ...days.map((d) => `<line class="ps-ws-day" x1="${d}" x2="${d}" y1="${top}" y2="${track}"/>`),
    ...wind.windows.map((w) => rect(`ps-ws-w${level(w)}`, w.start, w.end, top, base)),
    ...blew.filter((w) => w.start < t).map((w) => rect(`ps-ws-o${level(w)}`, w.start, Math.min(w.end, t), base + 1, track)),
    ...[[25, 6.5], [30, -1.5]].map(([kn, dy]) => `<g class="ps-ws-t${kn}"><line x1="0" x2="${W}" y1="${y(kn)}" y2="${y(kn)}"/><text x="${W}" y="${r(y(kn) + dy)}">${kn} kn</text></g>`),
    `<polyline class="ps-ws-fc" points="${nodes.map(([h, kn]) => `${x(h)},${y(kn)}`).join(" ")}"/>`,
    `<line class="ps-ws-cursor" x1="${x(t)}" x2="${x(t)}" y1="0" y2="${track}"/>`,
    `<text class="ps-ws-credit" x="0" y="45.5">${WIND_CREDIT}</text>`,
  ];
  return `<div class="ps-line ps-wind"><span>Wind h${wind.hour}</span> · <span>Port Control, issued ${escapeHtml(wind.time)}:</span> <span>≥25 kn ${spans(long(wind.windows))}</span> · <span>observed ${spans(long(wind.observed))}</span></div>
      <svg class="ps-wind-strip" width="${W}" height="48" viewBox="0 0 ${W} 48" role="img" aria-label="Wind forecast and observed windows">${strip.join("")}</svg>`;
}

const replanHtml = (r) => `${r.feasible ? r.cost : INFEASIBLE} <span class="muted">(reward ${fmtNum(r.reward, 3)})</span>`;

function bulletinsHtml(list, cls = "ps-msgs") {
  return list.length ? `<ul class="${cls}">${list.map((b) => `<li${b.new ? ' class="new"' : ""}>${b.time ? `<span class="muted">${escapeHtml(b.time)}</span> ` : ""}<b>${escapeHtml(b.from)}</b> ${escapeHtml(b.text)}</li>`).join("")}</ul>` : "";
}

function watchHeader(w, bulletins) {
  const line = w.index ? `freeze line h ${w.frozen_before}` : "every window open";
  return `<div class="ps-watch-h">Watch ${w.index} · ${escapeHtml(w.time)} (h ${w.hour}) · ${line}</div>${bulletinsHtml(bulletins)}`;
}

function resultHtml(task, step) {
  const r = step.result;
  if (r.error) return `<div class="res-line"><i class="dot bad"></i>${escapeHtml(r.error)}</div>`;
  const refused = (r.refused || []).length ? `<ul class="viol">${r.refused.map((x) => `<li>${escapeHtml(x.reason)}</li>`).join("")}</ul>` : "";
  const problems = (r.entry_problems || []).length ? `<ul class="viol">${r.entry_problems.map((p) => `<li>${escapeHtml(p)}</li>`).join("")}</ul>` : "";
  if (step.tool === "check_plan") return checkSummary(task, r) + (refused && `<div class="muted small">confirm_berths would refuse:</div>${refused}`) + problems;
  if (step.tool === "confirm_berths") return `<div class="res-line"><i class="dot ${r.refused.length ? "bad" : "ok"}"></i>Confirmed ${r.confirmed.length} · unchanged ${r.unchanged.length} · refused ${r.refused.length}</div>${refused}${problems}`;
  if (r.done) return `<div class="res-line"><i class="dot ${r.feasible ? "ok" : "bad"}"></i>Week done · ${r.feasible ? `feasible · cost ${r.cost}` : "infeasible"} · reward ${fmtNum(r.reward, 3)}</div>`;
  return `<div class="res-line">Watch ${r.watch} · ${escapeHtml(r.time)} · freeze line h ${r.frozen_before}</div><div class="muted small">berthed ${names(task, r.berthed)} · departed ${names(task, r.departed)}${r.unconfirmed.length ? ` · unconfirmed ${names(task, r.unconfirmed)}` : ""}</div>`;
}

function otherHtml(tc, out) {
  const res = parsed(out && out.content);
  if (res && res.situation) {
    return `<details class="plan-d"><summary>Watch ${res.watch} · ${escapeHtml(res.time)} · ${plural(res.windows.length, "window")}, ${res.unconfirmed.length} unconfirmed</summary><pre class="txt result">${escapeHtml(res.situation)}</pre></details>`;
  }
  const txt = String((out && out.content) ?? "");
  return `<details class="plan-d"><summary>Output <span class="muted">${escapeHtml(firstLine(txt))}</span></summary><pre class="txt result">${escapeHtml(txt)}</pre></details>`;
}

function gradeRows(gradeEl, ro) {
  const g = ro.final.grade;
  const ref = ro.live.reference;
  const count = (tool) => ro.steps.filter((s) => s.tool === tool).length;
  const kv = gradeEl.querySelector(".kv");
  for (const dt of kv.querySelectorAll("dt")) {
    if (dt.textContent === "Tool calls") dt.nextElementSibling.textContent = `${plural(count("check_plan"), "check")} · ${plural(count("confirm_berths"), "confirm")} · ${plural(count("advance"), "advance")}`;
    if (dt.textContent === "Naive re-plan") dt.nextElementSibling.innerHTML = ref.naive.feasible ? fmtNum(ref.naive.cost) : INFEASIBLE;
  }
  const audit = ro.live.audit;
  const wind = ref.hindsight_cost != null;
  const rows = [
    ["Excused cost", fmtNum(g.excused_cost), wind ? "Cost that news, or wind the forecast didn't show, brought to a window after its last chance to change: not charged" : "Cost that news brought to windows already frozen: not charged"],
    ["Regret", fmtNum(g.regret), wind ? "Cost above the optimum" : "Cost above the optimum in hindsight"],
    ["Rolling re-plan", replanHtml(ref.rolling), "A CP-SAT re-planner on the week as known, watch by watch"],
    ...extraRows(ref),
    ["Audit", audit.ok ? '<i class="dot ok"></i>passed' : `<i class="dot bad"></i>${escapeHtml(audit.problems.join("; "))}`, "Every bulletin arrived once, on time, at its watch"],
  ];
  if (wind) for (const dt of kv.querySelectorAll("dt")) if (dt.textContent === "Optimum") dt.title = "The lower of the best plan in hindsight and the forecast-following re-planner's cost";
  kv.insertAdjacentHTML("beforeend", rows.map(([k, v, tip]) => `<dt title="${escapeHtml(tip)}">${escapeHtml(k)}</dt><dd>${v}</dd>`).join(""));
}

/** A wind week's other references: the optimum in hindsight, and the re-planner blind to the forecast or holding every
 * warning. */
function extraRows(ref) {
  if (ref.hindsight_cost == null) return [];
  return [
    ["Hindsight", fmtNum(ref.hindsight_cost), "The best plan in hindsight, on the wind that blew"],
    ["Blind re-plan", replanHtml(ref.blind), "The rolling re-planner with the forecast taken out of its week"],
    ...(ref.hold ? [["Hold re-plan", replanHtml(ref.hold), "The rolling re-planner holding every window any forecast delivered so far showed"]] : []),
  ];
}

export function renderLive(root, ro, task, { onStep, horizon }) {
  const { live } = ro;
  const steps = ro.steps.map((s, k) => ({ ...s, last: k === ro.steps.length - 1 }));
  const stepOf = new Map(steps.map((s, k) => [s.call_id, k]));
  const outputs = new Map(ro.messages.filter((m) => m.role === "tool").map((m) => [m.tool_call_id, m]));
  const callEls = new Map();
  const charts = [];
  const state = { step: null, k: -1, t: 0, panel: "", key: null };
  const at = (via, k) => live.bulletins.filter((b) => b.via === via && (k == null || b.step === k));
  const weeks = new Map();
  /** The week as known at a step, one object for each set of bulletins, so the 3D quay rebuilds only on news. */
  const known = (step) => {
    const key = step.revealed.join(",");
    if (!weeks.has(key)) weeks.set(key, step.task);
    return weeks.get(key);
  };
  const watchLabel = (step) => `Watch ${step.watch}${step.last ? " (the last)" : ""}`;
  const truths = new Map();
  /** A wind week shown in the wind that blew, one object per week shown: the 3D quay draws it at the cursor hour. */
  const inTruth = (week) => truths.get(week) || truths.set(week, { ...week, rules: { ...week.rules, no_moves: task.rules.no_moves } }).get(week);

  root.innerHTML = "";
  let turn = 0;
  let next = 0;
  for (const m of ro.messages) {
    if (m.role === "system" || m.role === "user") {
      const d = document.createElement("details");
      d.className = `msg ${m.role}`;
      d.innerHTML = `<summary><span class="who">${m.role === "system" ? "System" : "User"}</span> <span class="muted">${escapeHtml(firstLine(m.content, 90))}</span></summary><pre class="txt">${escapeHtml(m.content)}</pre>`;
      root.appendChild(d);
      continue;
    }
    if (m.role !== "assistant") continue;
    if (++turn === 1) root.insertAdjacentHTML("beforeend", watchHeader(live.watches[0], at("load")));
    const d = document.createElement("div");
    d.className = "msg assistant";
    const ks = (m.tool_calls || []).map((tc) => stepOf.get(tc.id)).filter((k) => k != null);
    d.dataset.known = ks.length ? Math.min(...ks) : Math.min(next, steps.length - 1);
    if (ks.length) next = Math.max(...ks) + 1;
    d.innerHTML = `<div class="who">Assistant <span class="muted">· turn ${turn}</span></div>${m.reasoning ? `<details class="reason"><summary>Reasoning <span class="muted">${escapeHtml(firstLine(m.reasoning, 70))}</span></summary><pre class="txt">${escapeHtml(m.reasoning)}</pre></details>` : ""}${m.content && String(m.content).trim() ? `<div class="txt say">${escapeHtml(m.content)}</div>` : ""}`;
    const opened = [];
    let after = null;
    for (const tc of m.tool_calls || []) {
      const k = stepOf.get(tc.id);
      const step = steps[k];
      const out = outputs.get(tc.id);
      const call = document.createElement("div");
      call.className = `call${step ? " pick" : ""}`;
      let head = `<span class="fn">${escapeHtml(tc.name)}</span>`;
      let body = "";
      if (step && step.tool !== "advance") {
        const prev = step.tool === "check_plan" ? step.windows : k ? steps[k - 1].windows : [];
        const tbl = planTable(task, step.plan, prev);
        const n = Array.isArray(step.entries) ? step.entries.length : "?";
        head += ` <span class="muted">${n} entries · ${tbl.changed} changed</span>`;
        body += `<div class="mini-chart"></div><details class="plan-d"><summary>Plan table</summary>${tbl.html}</details>`;
      }
      if (step) {
        call.dataset.step = call.dataset.known = k;
        head += `<span class="step-no muted">step ${k + 1}</span>`;
        body += `<div class="result"${step.tool === "advance" ? ` data-known="${k}" data-arrive` : ""}>${resultHtml(task, step)}</div>`;
        if (step.tool === "advance" && !step.result.done) opened.push([step.watch, k]);
      } else body += otherHtml(tc, out);
      call.innerHTML = `<div class="call-h">${head}</div>${body}`;
      d.appendChild(call);
      if (!step) {
        if (after != null) Object.assign(call.dataset, { known: after, arrive: "" });
        continue;
      }
      after = k;
      callEls.set(k, call);
      call.addEventListener("click", (e) => {
        if (e.target.closest("summary, table, details[open] .plan-tbl")) return;
        onStep(k);
      });
      const host = call.querySelector(".mini-chart");
      if (host) {
        const ch = new BerthChart(host, { mini: true, onPick: () => onStep(k) });
        keepOverlay(ch, () => [step, step.hour]);
        ch.setData(known(step), evaluatePlan(known(step), step.plan), horizon);
        charts.push(ch);
      }
    }
    root.appendChild(d);
    for (const [w, k] of opened) root.appendChild(arriving(watchHeader(live.watches[w], at("trigger").filter((b) => b.watch === w)), k));
  }
  if (live.end_reason === "end_week") {
    root.appendChild(arriving(`<div class="ps-watch-h">End of the week · the env ran the remaining watches on the confirmed windows</div>${bulletinsHtml(at("env"))}`, steps.length - 1));
  }
  const later = [...root.querySelectorAll("[data-known]")];

  const left = root.closest(".ro-left");
  gradeRows(left.querySelector("#grade"), ro);
  const panel = document.createElement("section");
  panel.className = "ps-watch";
  left.insertBefore(panel, root.closest("section"));

  /** While the clock runs to the watch an advance opens, the week shown is still the one before it. */
  const shownAt = (t) => (state.k > 0 && state.step.tool === "advance" && !state.step.result.done && t < state.step.hour - 1e-6 ? steps[state.k - 1] : state.step);

  function renderPanel(t, shown) {
    const step = state.step;
    const st = statuses(shown, t);
    const counts = Object.fromEntries(STATUSES.map((s) => [s, shown.windows.filter((w) => st.get(w.ship) === s).length]));
    const c = clockAt(task, t);
    const seen = live.bulletins.filter((b) => b.step <= state.k && b.hour <= t).reverse();
    const feed = seen.map((b) => ({ ...b, new: b.hour === seen[0].hour }));
    const g = ro.final.grade;
    const ref = live.reference;
    const final = state.k === steps.length - 1
      ? `<dl class="kv ps-final"><dt>Reward</dt><dd><b>${fmtNum(g.reward, 3)}</b></dd><dt>Cost</dt><dd>${g.feasible ? g.cost : INFEASIBLE}</dd><dt>Excused cost</dt><dd>${fmtNum(g.excused_cost)}</dd><dt>Regret</dt><dd>${fmtNum(g.regret)}</dd><dt>Rolling re-plan</dt><dd>${replanHtml(ref.rolling)}</dd>${extraRows(ref).map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")}<dt>Naive re-plan</dt><dd>${replanHtml(ref.naive)}</dd><dt>Audit</dt><dd>${live.audit.ok ? '<i class="dot ok"></i>passed' : `<i class="dot bad"></i>${escapeHtml(live.audit.problems.join("; "))}`}</dd></dl>`
      : "";
    const next = shown === step ? "" : `<div class="ps-line ps-next">Advancing to watch ${step.watch}…</div>`;
    const html = `<div class="sec-head"><h2>${watchLabel(shown)}</h2><span class="muted small">step ${state.k + 1} of ${steps.length} · ${escapeHtml(step.tool)}</span></div>
      <div class="ps-clock"><b>${c.day} ${c.date} · ${c.hm}</b> <span class="muted">${virtualTime(task, t)}</span></div>${shown.marine ? marineHtml(shown.marine, t) : ""}${shown.wind ? windHtml(shown.wind, t, task.rules.no_moves, horizon) : ""}
      <div class="ps-line">${escapeHtml(shown.time)} (h ${shown.hour}) · ${shown.watch ? `freeze line h ${shown.frozen_before}` : "every window open"}</div>${next}
      <div class="ps-counts">${["departed", "berthed", "frozen", "open"].map((s) => `<span class="ps-c ps-${s}"><b>${counts[s]}</b> ${s}</span>`).join("")}<span class="ps-c"><b>${shown.unconfirmed.length}</b> unconfirmed</span></div>
      <div class="ps-known">${knownHtml(shown.known)}</div>
      ${feed.length ? bulletinsHtml(feed, "ps-feed") : '<p class="muted small">No news yet.</p>'}
      ${final}`;
    if (html !== state.panel) panel.innerHTML = state.panel = html;
  }

  const stage = currentStage();
  const { scene, chart } = stage;
  const title = left.parentElement.querySelector(".ro-right .chart-sec h2");
  keepOverlay(chart, () => [state.step && shownAt(state.t), state.t]);
  const chip = stage.tl.appendChild(Object.assign(document.createElement("span"), { className: "ovbox ps-chip" }));
  chip.hidden = true;

  /** The step viewer draws the selected plan on the real week; paint() draws the week shown instead. */
  let week = task;
  const setData = chart.setData.bind(chart);
  chart.setData = (_, ev, H) => setData(week, ev, H);
  const setEvaluation = stage.setEvaluation;
  stage.setEvaluation = () => {};

  function draw(shown) {
    week = shown.last ? task : known(shown);
    const quay = shown.wind ? inTruth(week) : week;
    if (scene.task !== quay) {
      const keep = { anim: scene.anim, userMoved: scene.userMoved };
      const [pos, target] = [scene.camera.position.clone(), scene.controls.target.clone()];
      scene.setTask(quay);
      scene._goto(pos, target, false);
      Object.assign(scene, keep);
    }
    setEvaluation(evaluatePlan(week, shown.plan));
  }

  function paint(t) {
    const shown = shownAt(t);
    const flying = shown !== state.step;
    const key = `${state.k}:${flying}`;
    if (key !== state.key) {
      state.key = key;
      draw(shown);
      for (const e of later) {
        const k = Number(e.dataset.known);
        e.classList.toggle("ps-future", k > state.k || (k === state.k && flying && "arrive" in e.dataset));
      }
      chip.hidden = false;
      chip.textContent = flying ? `Advancing to watch ${state.step.watch}…` : `${watchLabel(shown)} · ${shown.time}`;
      title.textContent = shown.last ? "Dock chart of the final plan, on the week as it turned out" : "Dock chart of the selected step, on the week as the planner knew it";
      stage.tl.querySelector("#step-status").innerHTML = knownHtml(shown.known);
      overlay(chart, shown, t);
    } else mark(chart, shown, t);
    renderPanel(t, shown);
  }

  const setTime = chart.setTime.bind(chart);
  chart.setTime = (t) => {
    setTime(t);
    state.t = t;
    if (state.step) paint(t);
  };

  return {
    select(k) {
      for (const [i, c] of callEls) c.classList.toggle("sel", i === k);
      const step = steps[k];
      if (!step) return;
      Object.assign(state, { step, k, key: null });
      stage.setTime(step.hour);
    },
    scrollTo(k) {
      const c = callEls.get(k);
      if (c) c.scrollIntoView({ block: "nearest", behavior: "smooth" });
    },
    destroy() {
      for (const c of charts) c.destroy();
    },
  };
}
