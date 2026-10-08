// The leaderboard and the episode table are adapted from PortSimEnv's overview.js (FineEnvs b0f4c2f, Apache-2.0).
import { getRun, getRuns } from "../api.js";
import { escapeHtml, fmtNum, fmtPct } from "../model.js";
import { nameOf as upstreamName } from "../overview.js?v=upstream";

const CONFIG = await fetch(new URL("/api/config", location.origin)).then((r) => r.json());
const UPSTREAM = "https://github.com/adithya-s-k/FineEnvs/tree/main/07-simulation-environments/portsim-v1";
const REPO = "https://github.com/earakely-scale/agentenv-portsim-plugin";
const DATASET = "https://huggingface.co/datasets/earakely-scale/PortSimEnv-AgentEnv";
const LINKS = [
  ["Run it yourself", `${DATASET}#play-a-week-yourself`, "play a week on your own machine, with agent-env and a Hugging Face token"],
  ["Dataset", DATASET, "the weeks, the references and every run here, as tables and as agent-env tasks"],
  ["agentenv-portsim", REPO, "the plugin: v1 and v2 as agent-env environments"],
  ["PortSimEnv", UPSTREAM, "the environment v1 comes from, its eval and this viewer, by Adithya S Kolavi"],
  ["Article", "https://huggingface.co/spaces/FineEnvs/simulation-rl-environments", "Simulation RL Environments, part 1"],
];
const VERSIONS = [
  { env: "portsim-live", v: "v2", name: "the live port", what: "the week unfolds watch by watch on a virtual clock, and the agent confirms berths as the news comes in" },
  { env: "portsim", v: "v1", name: "a week planned in one go", what: "the agent checks drafts and submits one plan, as in PortSimEnv" },
];
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
    { k: "task_id", label: "Week", get: (e) => e.task_id, html: (e) => `<a href="${runHref(e.run, e.model, e.task_id)}">${escapeHtml(e.task_id)}</a>` },
    { k: "difficulty", label: "Tier", get: (e) => e.difficulty, opt: true },
    { k: "ships", label: "Ships", get: (e) => e.ships, num: true, opt: true },
    { k: "result", label: "Result", get: (e) => e.end_reason, html: resultHtml, sort: (e) => (e.submitted ? 1 : 0) + (e.feasible ? 1 : 0) + (optimal(e) ? 1 : 0) },
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
    weeks: new Set(eps.map((e) => e.task_id)).size,
    mean: eps.reduce((a, e) => a + e.reward, 0) / eps.length,
    submitted: eps.filter((e) => e.submitted).length / eps.length,
    feasible: eps.filter((e) => e.feasible).length / eps.length,
    optimal: eps.filter(optimal).length,
  })).sort((a, b) => b.mean - a.mean);
}

function showcase(groups) {
  const first = groups[0];
  if (!first) return null;
  const order = first.boards.map((b) => b.model);
  return first.boards.flatMap((b) => b.eps).sort((a, b) =>
    optimal(b) - optimal(a) || (b.watches || 0) - (a.watches || 0) || a.task_id.localeCompare(b.task_id)
    || order.indexOf(a.model) - order.indexOf(b.model))[0];
}

export async function overviewPage({ app, setCrumbs, isCurrent, sortableTable }) {
  setCrumbs([]);
  app.innerHTML = `
  <div class="page ov-page ps-ov">
    <section class="ov-intro">
      <h1>PortSim on AgentEnv: model runs, replayed in 3D</h1>
      <p class="muted">Models re-plan a broken week of container-ship dockings at a Port of Barcelona quay on AgentEnv,
      replayed on PortSimEnv's viewer by Adithya S Kolavi (Apache-2.0): the quay in 3D, the dock chart of every plan the
      model checked or confirmed, the grade and the transcript. <b>v2, the live port</b>, plays the week as it unfolds
      and replays watch by watch: the virtual clock, the bulletins as they arrive, the windows as they freeze. <b>v1</b>
      plans the week in one go, as PortSimEnv does.</p>
      <ul class="ps-glossary muted small">
        <li><b>Week</b>: one task, a quay with its ships and what goes wrong. <b>Reward</b>: 1.0 for the optimum in hindsight, under 0.2 for a plan that breaks a rule, 0 for no plan.</li>
        <li><b>Watch</b> (v2): the time between two news bulletins. The agent re-plans each watch; a window starting within 6 hours is frozen.</li>
        <li><b>Optimum</b>, <b>rolling</b>, <b>naive</b>: the best plan CP-SAT finds in hindsight, a CP-SAT re-planner that only knows what has been announced, and a policy that pushes ships later. <b>Regret</b>: cost above the optimum.</li>
      </ul>
      <p class="muted small">Port of Barcelona twin © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a> (ODbL) · terrain: Terrain Tiles (AWS) · tasks: Port de Barcelona open data, CC BY-SA 4.0.</p>
      <dl class="kv">${LINKS.map(([k, href, what]) => `<dt><a class="ext" href="${href}" target="_blank" rel="noopener">${k} ↗</a></dt><dd class="muted">${what}</dd>`).join("")}</dl>
    </section>
    <section class="ps-start" hidden></section>
    <div id="ps-runs"><p class="muted">Loading runs…</p></div>
    <section class="ov-eps" hidden>
      <div class="sec-head"><h2 id="ov-eps-h">Weeks</h2><span class="muted small" id="ov-eps-note"></span></div>
      <table class="tbl click" id="ov-eps"><thead></thead><tbody></tbody></table>
    </section>
  </div>`;
  const runs = await getRuns();
  const episodes = new Map(await Promise.all(runs.map(async (r) => [r.run, (await getRun(r.run)).episodes])));
  if (!isCurrent()) return;
  const groups = VERSIONS.map((ver) => {
    const own = runs.filter((r) => r.env === ver.env);
    return {
      ...ver,
      runs: own,
      boards: board(own.flatMap((r) => episodes.get(r.run).map((e) => ({ ...e, run: r.run })))),
      failed: own.flatMap((r) => r.failed),
      caps: [...new Set(own.map((r) => r.episode_cap_usd))].sort((a, b) => a - b),
    };
  }).filter((g) => g.runs.length && g.boards.length);

  const start = showcase(groups);
  if (start) {
    const sec = app.querySelector(".ps-start");
    sec.hidden = false;
    sec.innerHTML = `<b>Start here:</b> ${escapeHtml(nameOf(start.model))} plays the ${start.watches ? "live " : ""}week
      <code>${escapeHtml(start.task_id)}</code>${start.watches ? ` over ${start.watches} watches` : ""} and scores
      ${fmtNum(start.reward, 3)}. <a href="${runHref(start.run, start.model, start.task_id)}">▶ Replay it</a>`;
  }

  app.querySelector("#ps-runs").innerHTML = groups.length
    ? groups.map((g) => `<section class="ps-run">
        <div class="sec-head"><h2>${g.v} · ${escapeHtml(g.name)}</h2><span class="muted small">${escapeHtml(g.what)} · env ${escapeHtml(g.env)} · model spend capped at ${g.caps.map((c) => `$${c}`).join(" to ")} an episode</span></div>
        <table class="tbl click"><thead><tr><th>Model</th><th class="num">Weeks</th><th class="num">Mean reward</th><th class="num">${g.env === "portsim-live" ? "Reached the end" : "Submitted"}</th><th class="num">Feasible</th><th class="num">Optimal</th></tr></thead>
        <tbody>${g.boards.map((b) => `<tr data-row="${escapeHtml(b.model)}" data-env="${escapeHtml(g.env)}" title="List ${escapeHtml(nameOf(b.model))}'s weeks"><td><span title="${escapeHtml(b.model)}">${escapeHtml(nameOf(b.model))}</span></td><td class="num">${b.weeks}${b.n > b.weeks ? ` (${b.n} runs)` : ""}</td><td class="num"><b>${fmtNum(b.mean, 3)}</b></td><td class="num">${fmtPct(b.submitted)}</td><td class="num">${fmtPct(b.feasible)}</td><td class="num">${b.optimal}/${b.n}</td></tr>`).join("")}</tbody></table>
        <p class="muted small">From the sweep${g.runs.length > 1 ? "s" : ""} ${g.runs.map((r) => `<code>${escapeHtml(r.run)}</code>`).join(", ")}.</p>
        ${g.failed.length ? `<ul class="viol">${g.failed.map((f) => `<li>${escapeHtml(nameOf(f.model))} on ${escapeHtml(f.task_id)} does not replay: ${escapeHtml(f.error)}</li>`).join("")}</ul>` : ""}
      </section>`).join("")
    : '<p class="muted">No runs.</p>';

  const epsSec = app.querySelector(".ov-eps");
  function select(env, model) {
    const g = groups.find((x) => x.env === env);
    const b = g.boards.find((x) => x.model === model);
    for (const tr of app.querySelectorAll("#ps-runs tr[data-row]")) tr.classList.toggle("sel", tr.dataset.env === env && tr.dataset.row === model);
    epsSec.hidden = false;
    app.querySelector("#ov-eps-h").textContent = `Weeks · ${nameOf(model)} · ${g.v}, ${g.name}`;
    app.querySelector("#ov-eps-note").textContent = `${model} · ${b.weeks} weeks · click one to replay it in 3D`;
    app.querySelector("#ov-eps").replaceChildren(document.createElement("thead"), document.createElement("tbody"));
    sortableTable(app.querySelector("#ov-eps"), columns(env === "portsim-live"), b.eps, {
      initial: { key: "task_id", dir: 1 },
      rowAttrs: (e) => `data-row="${escapeHtml(`${e.run}|${e.task_id}`)}"`,
      onRow: (key) => {
        const [run, task] = key.split("|");
        location.hash = runHref(run, model, task);
      },
    });
  }
  app.querySelector("#ps-runs").addEventListener("click", (e) => {
    const tr = e.target.closest("tr[data-row]");
    if (!tr) return;
    select(tr.dataset.env, tr.dataset.row);
    epsSec.scrollIntoView({ block: "start", behavior: "smooth" });
  });
  if (groups.length) select(groups[0].env, groups[0].boards[0].model);
}
