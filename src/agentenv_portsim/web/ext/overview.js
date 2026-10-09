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
  ["agentenv-portsim", REPO, "the plugin: v1 to v4 as agent-env environments"],
  ["PortSimEnv", UPSTREAM, "the environment v1 comes from, its eval and this viewer, by Adithya S Kolavi"],
  ["Article", "https://huggingface.co/spaces/FineEnvs/simulation-rl-environments", "Simulation RL Environments, part 1"],
];
const VERSIONS = [
  { env: "portsim-wind", v: "v4", name: "the wind port", what: "the marine port in real Barcelona storms, planned on the forecasts as issued and graded on the wind that blew" },
  { env: "portsim-marine", v: "v3", name: "the marine port", what: "the live week with the port's pilots and tugs, shared with the rest of the port's real traffic" },
  { env: "portsim-live", v: "v2", name: "the live port", what: "the week unfolds watch by watch on a virtual clock, and the agent confirms berths as the news comes in" },
  { env: "portsim", v: "v1", name: "a week planned in one go", what: "the agent checks drafts and submits one plan, as in PortSimEnv" },
];
const enc = encodeURIComponent;
const runHref = (run, model, task) => `#/run/${enc(run)}/${enc(model)}/${enc(task)}`;
const optimal = (e) => (e.reward || 0) >= 0.999;

const NAMES = {
  "anthropic/claude-opus-5-5": "Claude Opus 5.5",
  "anthropic/claude-haiku-5-5": "Claude Haiku 5.5",
  "openai/gpt-6-astra": "GPT-6 Astra",
  "openai/gpt-6-luna": "GPT-6 Luna",
  "fireworks_ai/kimi-k3": "Kimi K3",
  "fireworks_ai/deepseek-v4p1-flash": "DeepSeek V4.1 Flash",
};

export const nameOf = (model) => NAMES[model] ?? upstreamName(CONFIG.published[model] ?? model);

function resultHtml(e) {
  if (!e.submitted) return `<span class="muted">${escapeHtml(e.end_reason || "not submitted")}</span>`;
  if (!e.feasible) return '<i class="dot bad"></i>rule broken';
  return optimal(e) ? '<i class="dot ok"></i>optimal' : '<i class="dot ok"></i>valid';
}

function columns(env) {
  const live = env !== "portsim";
  const cols = [
    { k: "task_id", label: "Week", get: (e) => e.task_id, html: (e) => `<a href="${runHref(e.run, e.model, e.task_id)}">${escapeHtml(e.task_id)}</a>` },
    { k: "difficulty", label: "Tier", get: (e) => e.difficulty, opt: true },
    { k: "ships", label: "Ships", get: (e) => e.ships, num: true, opt: true },
    { k: "result", label: "Result", get: (e) => e.end_reason, html: resultHtml, sort: (e) => (e.submitted ? 1 : 0) + (e.feasible ? 1 : 0) + (optimal(e) ? 1 : 0) },
    { k: "cost", label: "Cost", get: (e) => (e.feasible ? e.cost : "–"), sort: (e) => (e.feasible ? e.cost : null), num: true },
    { k: "optimal_cost", label: env === "portsim-wind" ? "Anchor" : "Optimum", get: (e) => e.optimal_cost, num: true, opt: true, title: env === "portsim-wind" ? "The lower of the best plan in hindsight and the forecast-following re-planner's cost" : undefined },
    { k: "naive_cost", label: "Naive", get: (e) => e.naive_cost ?? (live ? "infeasible" : null), sort: (e) => e.naive_cost, num: true, opt: true, title: "The naive policy's cost; infeasible when its plan breaks a rule" },
  ];
  if (live) {
    cols.push({ k: "rolling_cost", label: "Rolling", get: (e) => e.rolling_cost, num: true, opt: true, title: "Cost of the rolling CP-SAT re-planner on the same week" });
    if (env === "portsim-wind") {
      cols.push({ k: "hindsight_cost", label: "Hindsight", get: (e) => e.hindsight_cost, num: true, opt: true, title: "The best plan in hindsight, on the wind that blew. It pays for all the wind, while a plan that follows the forecast is not charged for wind no forecast showed, so it can cost less" });
      cols.push({ k: "weather", label: "Weather", get: (e) => e.weather, opt: true, title: "The weather week the week was played in" });
    }
    cols.push({ k: "watches", label: "Watches", get: (e) => e.watches, num: true, opt: true });
    cols.push({ k: "regret", label: "Regret", get: (e) => e.regret ?? "–", sort: (e) => e.regret, num: true, title: env === "portsim-wind" ? "Cost above the anchor" : "Cost above the optimum in hindsight" });
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

function capsText(caps) {
  const values = new Set(caps.values());
  if (values.size === 1) return `model spend capped at $${[...values][0]} an episode`;
  return `model spend capped per episode at ${[...caps].map(([m, c]) => `$${c} for ${nameOf(m)}`).join(", ")}`;
}

/** The run the README and the cards film and link: GPT-6.1 Sol's wind week with the berth no forecast showed. */
const FEATURED = { run: "wind-pilot-gpt", model: "openai/gpt-6.1-sol", task_id: "dock-24B-w37x1-standard-0-e01" };

function showcase(groups) {
  const first = groups[0];
  if (!first) return null;
  const featured = first.boards.flatMap((b) => b.eps).find((e) =>
    e.run === FEATURED.run && e.model === FEATURED.model && e.task_id === FEATURED.task_id);
  if (featured) return { ...featured, group: first };
  const order = first.boards.map((b) => b.model);
  const best = first.boards.flatMap((b) => b.eps).sort((a, b) =>
    optimal(b) - optimal(a) || (b.watches || 0) - (a.watches || 0) || a.task_id.localeCompare(b.task_id)
    || order.indexOf(a.model) - order.indexOf(b.model))[0];
  return best && { ...best, group: first };
}

export async function overviewPage({ app, setCrumbs, isCurrent, sortableTable }) {
  setCrumbs([]);
  app.innerHTML = `
  <div class="page ov-page ps-ov">
    <section class="ov-intro">
      <h1>PortSimEnv on AgentEnv: model runs, replayed in 3D</h1>
      <p class="muted">Models re-plan a broken week of container-ship dockings at a Port of Barcelona quay on AgentEnv,
      replayed on PortSimEnv's viewer by Adithya S Kolavi (Apache-2.0): the quay in 3D, the dock chart of every plan the
      model checked or confirmed, the grade and the transcript. <b>v4, the wind port</b>, plays the marine port in real
      Barcelona storms: at every watch the agent gets the wind forecast issued by then, and the week is graded on the wind
      that blew. <b>v3, the marine port</b>, is the live port with the port's pilots and tugs, shared with its real 2024
      traffic. <b>v2, the live port</b>, plays the week as it unfolds
      and replays watch by watch: the virtual clock, the bulletins as they arrive, the windows as they freeze. <b>v1</b>
      plans the week in one go, as PortSimEnv does.</p>
      <ul class="ps-glossary muted small">
        <li><b>Week</b>: one task, a quay with its ships and what goes wrong; a v1 task can span up to three weeks (<code>x2</code>, <code>x3</code> in its id), a v2, v3 or v4 week is always one, and a v4 week's id ends with its weather week (<code>-e09</code>). <b>Reward</b>: 1.0 for the optimum, under 0.2 for a plan that breaks a rule, 0 for no plan.</li>
        <li><b>Watch</b> (v2 to v4): watch 0 opens the week at hour 0, and a new watch starts at each news bulletin; in v4 also at 00:00 or 12:00 when a new forecast restricts hours the last one didn't. The agent re-plans each watch; a window starting within 6 hours is frozen.</li>
        <li><b>Pilots and tugs</b> (v3, v4): a pilot is the local mariner who boards to guide a ship in or out, and tugs are the boats that push and pull it alongside. Each berthing and departure of a ship of 45 m or more takes a pilot, and tugs by its length, in its hour, from 7 pilots and 8 tugs the quay shares with the port's other 2024 traffic; an hour our ships need more than are free is short, which breaks a rule. Sweeps named <code>…-pilot-…</code> are small first batches, not pilots.</li>
        <li><b>Wind</b> (v4): above 25 kn at the port's anemometer ships of 300 m or more may not berth or leave, and every movement takes one more tug; above 30 kn no ship moves. The wind is read at Meteocat's XEMA station Y7 (Bocana Sud), which stands in for the ordinance's anemometer at the Dique Sur, and the rules follow the wind that blew. At each watch a Barcelona Port Control bulletin, standing in for the port's own forecasts, gives the ECMWF run published by then, adjusted to that anemometer. Wind the forecast didn't show, like news, is excused on a window frozen before it was known; wind it showed is charged. Hours <code>a–b</code> run from hour a up to, not including, b. A v4 week keeps its schedule's 2024 dates; its wind is from a week of 2023 to 2025.</li>
        <li><b>Optimum</b>, <b>rolling</b>, <b>naive</b>: the best plan CP-SAT finds in hindsight, a CP-SAT re-planner that only knows what has been announced, and a simple policy that pushes ships later (in v2 to v4, it keeps each confirmed window that still fits and moves the rest, knowing nothing of pilots and tugs). In v4 a week is scored against the <b>anchor</b>, the lower of the best plan in hindsight and the cost of the rolling re-planner, which follows the forecasts; hindsight pays for all the wind, while a plan that follows the forecast is not charged for wind no forecast showed, so it can cost less. <b>Blind</b> is that re-planner with the forecast taken away. <b>Regret</b>: cost above the optimum, in v4 above the anchor.</li>
      </ul>
      <p class="muted small">Port of Barcelona twin © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a> (ODbL) · terrain: Terrain Tiles (AWS) · tasks: Port de Barcelona open data, CC BY-SA 4.0 · v4 wind: forecasts contain modified ECMWF open data (CC BY 4.0), observed windows derived from the Servei Meteorològic de Catalunya's (Meteocat) XEMA station Y7.</p>
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
      weeks: new Set(own.flatMap((r) => episodes.get(r.run).map((e) => e.task_id))).size,
      caps: new Map(own.flatMap((r) => r.models.map((m) => [m, r.episode_cap_usd]))),
    };
  }).filter((g) => g.runs.length && g.boards.length);

  const start = showcase(groups);
  if (start) {
    const sec = app.querySelector(".ps-start");
    sec.hidden = false;
    sec.innerHTML = `<b>Start here:</b> ${escapeHtml(nameOf(start.model))} plays the ${start.group.v} week
      <code>${escapeHtml(start.task_id)}</code> (${escapeHtml(start.group.name)})${start.watches ? ` over ${start.watches} watches` : ""} and scores
      ${fmtNum(start.reward, 3)}. <a href="${runHref(start.run, start.model, start.task_id)}">▶ Replay it</a>`;
  }

  app.querySelector("#ps-runs").innerHTML = groups.length
    ? groups.map((g) => `<section class="ps-run">
        <div class="sec-head"><h2>${g.v} · ${escapeHtml(g.name)}</h2><span class="muted small">${escapeHtml(g.what)} · env ${escapeHtml(g.env)} · ${escapeHtml(capsText(g.caps))}</span></div>
        <table class="tbl click"><thead><tr><th>Model</th><th class="num">Weeks</th><th class="num">Mean reward</th><th class="num">${g.env !== "portsim" ? "Reached the end" : "Submitted"}</th><th class="num">Feasible</th><th class="num">${g.env === "portsim-wind" ? "At the anchor" : "Optimal"}</th></tr></thead>
        <tbody>${g.boards.map((b) => `<tr data-row="${escapeHtml(b.model)}" data-env="${escapeHtml(g.env)}" title="List ${escapeHtml(nameOf(b.model))}'s weeks"><td><span title="${escapeHtml(b.model)}">${escapeHtml(nameOf(b.model))}</span></td><td class="num">${b.weeks}${b.weeks < g.weeks ? ` of ${g.weeks}` : ""}${b.n > b.weeks ? ` (${b.n} runs)` : ""}</td><td class="num"><b>${fmtNum(b.mean, 3)}</b></td><td class="num">${fmtPct(b.submitted)}</td><td class="num">${fmtPct(b.feasible)}</td><td class="num">${b.optimal}/${b.n}</td></tr>`).join("")}</tbody></table>
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
    sortableTable(app.querySelector("#ov-eps"), columns(env), b.eps, {
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
