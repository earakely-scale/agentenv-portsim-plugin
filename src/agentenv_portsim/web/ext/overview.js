// The leaderboard and the episode table are adapted from PortSimEnv's overview.js (FineEnvs b0f4c2f, Apache-2.0).
import { getRun, getRuns } from "../api.js";
import { escapeHtml, fmtNum, fmtPct } from "../model.js";
import { nameOf as upstreamName } from "../overview.js?v=upstream";

const CONFIG = await fetch(new URL("/api/config", location.origin)).then((r) => r.json());
const UPSTREAM = "https://github.com/adithya-s-k/FineEnvs/tree/main/07-simulation-environments/portsim-v1";
const REPO = "https://github.com/earakely-scale/agentenv-portsim-plugin";
const LINKS = [
  ["PortSimEnv", UPSTREAM, "the environment, its eval and this viewer, by Adithya S Kolavi"],
  ["Article", "https://huggingface.co/spaces/FineEnvs/simulation-rl-environments", "Simulation RL Environments, part 1"],
  ["agentenv-portsim", REPO, "v1 and v2, the live port, as agent-env environments, and the sweeps"],
];
const ENVS = {
  "portsim-live": ["v2", "the live port: the week unfolds watch by watch on a virtual clock"],
  portsim: ["v1", "a week planned in one go: one plan, one graded submit"],
};
const versionOf = (env) => (ENVS[env] || [""])[0];
const enc = encodeURIComponent;
const runHref = (run, model, task) => `#/run/${enc(run)}/${enc(model)}/${enc(task)}`;
const optimal = (e) => (e.reward || 0) >= 0.999;

export const nameOf = (model) => upstreamName(CONFIG.published[model] ?? model);

function resultHtml(e) {
  if (!e.submitted) return `<span class="muted">${escapeHtml(e.end_reason || "not submitted")}</span>`;
  if (!e.feasible) return '<i class="dot bad"></i>rule broken';
  return optimal(e) ? '<i class="dot ok"></i>optimal' : '<i class="dot ok"></i>valid';
}

function columns(live) {
  const cols = [
    { k: "task_id", label: "Task", get: (e) => e.task_id, html: (e) => `<a href="${runHref(e.run, e.model, e.task_id)}">${escapeHtml(e.task_id)}</a>` },
    { k: "difficulty", label: "Tier", get: (e) => e.difficulty, opt: true },
    { k: "ships", label: "Ships", get: (e) => e.ships, num: true, opt: true },
    { k: "result", label: live ? "Week" : "Result", get: (e) => e.end_reason, html: resultHtml, sort: (e) => (e.submitted ? 1 : 0) + (e.feasible ? 1 : 0) + (optimal(e) ? 1 : 0) },
    { k: "cost", label: "Cost", get: (e) => (e.feasible ? e.cost : "–"), sort: (e) => (e.feasible ? e.cost : null), num: true },
    { k: "optimal_cost", label: "Optimum", get: (e) => e.optimal_cost, num: true, opt: true },
    { k: "naive_cost", label: "Naive", get: (e) => e.naive_cost, num: true, opt: true },
  ];
  if (live) {
    cols.push({ k: "rolling_cost", label: "Rolling", get: (e) => e.rolling_cost, num: true, opt: true, title: "Cost of the rolling CP-SAT re-planner on the same week" });
    cols.push({ k: "watches", label: "Watches", get: (e) => e.watches, num: true, opt: true });
    cols.push({ k: "regret", label: "Regret", get: (e) => e.regret ?? "–", sort: (e) => e.regret, num: true, title: "Cost above the optimum in hindsight" });
  } else cols.push({ k: "checks", label: "Checks", get: (e) => e.checks, num: true, opt: true });
  cols.push({ k: "reward", label: "Reward", get: (e) => fmtNum(e.reward, 3), sort: (e) => e.reward, num: true });
  return cols;
}

function board(episodes) {
  const by = new Map();
  for (const e of episodes) by.set(e.model, [...(by.get(e.model) || []), e]);
  return [...by].map(([model, eps]) => ({
    model,
    eps,
    n: eps.length,
    mean: eps.reduce((a, e) => a + e.reward, 0) / eps.length,
    submitted: eps.filter((e) => e.submitted).length / eps.length,
    feasible: eps.filter((e) => e.feasible).length / eps.length,
    optimal: eps.filter(optimal).length,
  })).sort((a, b) => b.mean - a.mean);
}

export async function overviewPage({ app, setCrumbs, isCurrent, sortableTable }) {
  setCrumbs([]);
  app.innerHTML = `
  <div class="page ov-page ps-ov">
    <section class="ov-intro">
      <h1>PortSim runs: agent-env sweeps, replayed in 3D</h1>
      <p class="muted">Models re-plan a broken week of container-ship dockings at a Port of Barcelona quay, through
      agent-env sweeps, replayed on PortSimEnv's viewer by Adithya S Kolavi (Apache-2.0): the quay in 3D, the dock
      chart of every plan the model checked or confirmed, the grade and the transcript. <b>v2, the live port</b>, plays
      the week as it unfolds and replays watch by watch: the virtual clock, the bulletins as they arrive, the windows as
      they freeze. <b>v1</b> plans the week in one go, as PortSimEnv does.</p>
      <p class="muted small">Port of Barcelona twin © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a> (ODbL) · terrain: Terrain Tiles (AWS) · tasks: Port de Barcelona open data, CC BY-SA 4.0.</p>
      <dl class="kv">${LINKS.map(([k, href, what]) => `<dt><a class="ext" href="${href}" target="_blank" rel="noopener">${k} ↗</a></dt><dd class="muted">${what}</dd>`).join("")}</dl>
    </section>
    <div id="ps-runs"><p class="muted">Loading runs…</p></div>
    <section class="ov-eps" hidden>
      <div class="sec-head"><h2 id="ov-eps-h">Episodes</h2><span class="muted small" id="ov-eps-note"></span></div>
      <table class="tbl click" id="ov-eps"><thead></thead><tbody></tbody></table>
    </section>
  </div>`;
  const runs = (await getRuns()).sort((a, b) => versionOf(b.env).localeCompare(versionOf(a.env)));
  const boards = new Map(await Promise.all(runs.map(async (r) => [r.run, board((await getRun(r.run)).episodes)])));
  if (!isCurrent()) return;
  app.querySelector("#ps-runs").innerHTML = runs.length
    ? runs.map((r) => `<section class="ps-run">
        <div class="sec-head"><h2>${escapeHtml(versionOf(r.env))} · ${escapeHtml(r.run)}</h2><span class="muted small">${escapeHtml(r.env)} · ${escapeHtml((ENVS[r.env] || [])[1] || "")} · ${r.episodes} episodes${r.k > 1 ? ` · rep ${r.rep} of ${r.k}` : ""} · cap $${r.episode_cap_usd} an episode</span></div>
        <table class="tbl click"><thead><tr><th>Model</th><th class="num">Episodes</th><th class="num">Mean</th><th class="num">${r.env === "portsim-live" ? "Reached done" : "Submitted"}</th><th class="num">Feasible</th><th class="num">Optimal</th></tr></thead>
        <tbody>${boards.get(r.run).map((b) => `<tr data-row="${escapeHtml(b.model)}" data-run="${escapeHtml(r.run)}" title="List ${escapeHtml(nameOf(b.model))}'s episodes"><td><span title="${escapeHtml(b.model)}">${escapeHtml(nameOf(b.model))}</span></td><td class="num">${b.n}</td><td class="num"><b>${fmtNum(b.mean, 3)}</b></td><td class="num">${fmtPct(b.submitted)}</td><td class="num">${fmtPct(b.feasible)}</td><td class="num">${b.optimal}/${b.n}</td></tr>`).join("")}</tbody></table>
        ${r.failed.length ? `<ul class="viol">${r.failed.map((f) => `<li>${escapeHtml(nameOf(f.model))} on ${escapeHtml(f.task_id)} does not replay: ${escapeHtml(f.error)}</li>`).join("")}</ul>` : ""}
      </section>`).join("")
    : '<p class="muted">No runs.</p>';

  const epsSec = app.querySelector(".ov-eps");
  function select(run, model) {
    const r = runs.find((x) => x.run === run);
    const b = boards.get(run).find((x) => x.model === model);
    for (const tr of app.querySelectorAll("#ps-runs tr[data-row]")) tr.classList.toggle("sel", tr.dataset.run === run && tr.dataset.row === model);
    epsSec.hidden = false;
    app.querySelector("#ov-eps-h").textContent = `Episodes · ${nameOf(model)} · ${versionOf(r.env)} · ${run}`;
    app.querySelector("#ov-eps-note").textContent = `${model} · ${b.n} episodes · click one to replay it in 3D`;
    const rows = b.eps.map((e) => ({ ...e, run }));
    app.querySelector("#ov-eps").replaceChildren(document.createElement("thead"), document.createElement("tbody"));
    sortableTable(app.querySelector("#ov-eps"), columns(r.env === "portsim-live"), rows, {
      initial: { key: "task_id", dir: 1 },
      rowAttrs: (e) => `data-row="${escapeHtml(e.task_id)}"`,
      onRow: (task) => (location.hash = runHref(run, model, task)),
    });
  }
  app.querySelector("#ps-runs").addEventListener("click", (e) => {
    const tr = e.target.closest("tr[data-row]");
    if (!tr) return;
    select(tr.dataset.run, tr.dataset.row);
    epsSec.scrollIntoView({ block: "start", behavior: "smooth" });
  });
  const first = runs.find((r) => boards.get(r.run).length);
  if (first) select(first.run, boards.get(first.run)[0].model);
}
