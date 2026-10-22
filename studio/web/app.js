"use strict";
const $ = (selector) => document.querySelector(selector);
const state = {katas: [], runs: [], kata: null, runId: null, events: [], mode: "live", cursor: 0, playback: null, source: null, selected: null, target: "solution", tab: "workspace", active: null, viewVersion: 0, launching: false};
const glyphs = ["{ }", "[✓]", "ƒ(x)", "⑂", "↻", "≤", "⇄", "◇", "⛓", "⑃", "▥"];
let paintTimer;
function el(tag, className, text) {const node = document.createElement(tag); if (className) node.className = className; if (text !== undefined) node.textContent = text; return node;}
function button(text, className, action) {const node = el("button", className, text); node.type = "button"; node.addEventListener("click", action); return node;}
function pill(text, status = "") {return el("span", `pill ${status}`, text);}
function toast(message) {$("#toast").textContent = message; $("#toast").hidden = false; setTimeout(() => {$("#toast").hidden = true;}, 6500);}
async function api(path, options) {const response = await fetch(path, options); const data = await response.json(); if (!response.ok) throw Error(data.error || "Request failed"); return data;}
async function refresh() {const [catalog, history] = await Promise.all([api("/api/katas"), api("/api/runs")]); state.katas = catalog.katas; state.runs = history.runs; state.active = history.active_run;}
function cleanup() {if (state.source) state.source.close(); state.source = null; pause(); clearTimeout(paintTimer); state.selected = null;}
function nav() {
  $("#kata-nav").replaceChildren(...state.katas.map((kata, index) => {
    const item = button("", `kata-link ${state.kata?.id === kata.id ? "active" : ""}`, () => openKata(kata.id));
    item.append(el("span", "num", String(index + 1).padStart(2, "0")), el("span", "name", kata.title), el("span", `tiny-dot ${kata.available ? "" : "planned"}`));
    item.title = `${kata.title}: ${kata.available ? "Available" : "Planned"}`;
    return item;
  }));
  $("#home-nav").classList.toggle("active", !state.kata && state.tab !== "history");
  $("#history-nav").classList.toggle("active", state.tab === "history");
}
async function home() {
  const version = ++state.viewVersion;
  cleanup(); state.kata = null; state.tab = "overview";
  try {await refresh();} catch (error) {toast(error.message); return;}
  if (version !== state.viewVersion) return;
  nav(); $("#breadcrumb").textContent = "Overview";
  const main = $("#main"); main.replaceChildren();
  const hero = el("section", "hero"), intro = el("div"); intro.append(el("div", "eyebrow", "THE PRACTICE OF BUILDING RELIABLE AI"));
  const heading = el("h1"); heading.append("Small tests.", document.createElement("br"), el("em", "", "Visible progress."));
  intro.append(heading, el("p", "", "Explore the contracts behind reliable AI. Write a test, follow the execution, and understand every small step forward."));
  const art = el("div", "hero-art"); art.setAttribute("aria-hidden", "true"); art.append(el("div", "cycle"), el("div", "cycle-center", "ONE SMALL\nSTEP AT A TIME"), el("div", "cycle-pill red", "● RED / make it fail"), el("div", "cycle-pill green", "● GREEN / make it work"), el("div", "cycle-pill refactor", "◇ REFACTOR / make it clear"));
  hero.append(intro, art); main.append(hero);
  const available = state.katas.filter(k => k.available).length;
  const stats = el("section", "stats");
  [["◫", `${available}`, `/ ${state.katas.length} katas`, "Available to explore"], ["↻", String(state.runs.length), "saved runs", "Real events. Replayable learning."], ["◇", "0", "API calls", "Offline test runner"]].forEach(([icon, value, caption, desc]) => {
    const stat = el("div", "stat"), text = el("div"), count = el("b", "", value + " "); count.append(el("small", "", caption)); text.append(count, el("p", "", desc)); stat.append(el("span", "stat-icon", icon), text); stats.append(stat);
  }); main.append(stats);
  const title = el("div", "section-title"), text = el("div"); text.append(el("h2", "", "Your learning path"), el("p", "", "One boundary at a time. Start anywhere; build understanding as you go.")); title.append(text, pill("11 EXERCISES · PYTHON")); main.append(title);
  const cards = el("section", "cards");
  state.katas.forEach((kata, index) => {
    const card = el("article", `kata-card ${kata.available ? "available" : "planned-card"}`), top = el("div", "card-top"); top.append(el("span", "card-number", `KATA ${String(index + 1).padStart(2, "0")}`), pill(kata.available ? "Available" : "Planned", kata.available ? "" : "planned"));
    card.append(top, el("div", "card-glyph", glyphs[index]), el("h3", "", kata.title), el("p", "", kata.description));
    const footer = el("div", "card-footer"), last = state.runs.find(run => run.kata_id === kata.id);
    footer.append(el("small", "", last ? `Latest: ${last.status} · ${last.target}` : kata.available ? "Not run yet" : "Not implemented"), button(kata.available ? "Open workspace ↗" : "Preview ↗", "text-button", () => openKata(kata.id)));
    card.append(footer); cards.append(card);
  }); main.append(cards);
}
async function openKata(id, runId = null) {
  const version = ++state.viewVersion;
  cleanup(); state.tab = "workspace"; state.runId = null; state.events = []; state.mode = "live";
  let kata;
  try {await refresh(); kata = await api(`/api/katas/${encodeURIComponent(id)}`);} catch (error) {toast(error.message); return;}
  if (version !== state.viewVersion) return;
  state.kata = kata;
  state.target = state.kata.targets.includes(state.target) ? state.target : "solution"; nav(); $("#breadcrumb").textContent = state.kata.title;
  const main = $("#main"); main.replaceChildren();
  const heading = el("div", "workspace-heading"), intro = el("div"); intro.append(el("div", "eyebrow", `KATA ${id.slice(0, 2)} / ${state.kata.available ? "AVAILABLE" : "PLANNED"}`), el("h1", "", state.kata.title), el("p", "", state.kata.tagline + " " + state.kata.description));
  const controls = el("div", "controls"), label = el("label", "", "Target"); label.htmlFor = "target";
  const target = el("select"); target.id = "target"; target.setAttribute("aria-label", "Implementation target");
  (state.kata.targets.length ? state.kata.targets : ["solution"]).forEach(value => {const option = el("option", "", value === "working" ? "Working copy" : value === "starter" ? "Starter (exercise)" : "Reference solution"); option.value = value; target.append(option);}); target.value = state.target;
  target.addEventListener("change", () => {state.target = target.value;}); target.disabled = !state.kata.available;
  const run = button("▶  Run tests", "btn primary", startRun); run.id = "run-button"; run.disabled = !state.kata.available || Boolean(state.active);
  controls.append(label, target, run); heading.append(intro, controls); main.append(heading);
  const tabs = el("div", "tabs"); [["workspace", "Execution workspace"], ["guide", "Kata instructions"]].forEach(([id, text]) => {const tab = button(text, `tab ${id === "workspace" ? "active" : ""}`, () => {state.tab = id; document.querySelectorAll(".tab").forEach(n => n.classList.toggle("active", n === tab)); $("#workspace").hidden = id !== "workspace"; $("#guide").hidden = id !== "guide";}); tabs.append(tab);}); main.append(tabs);
  const guide = el("pre", "guide", state.kata.guide); guide.id = "guide"; guide.hidden = true;
  const workspace = el("div"); workspace.id = "workspace";
  if (!state.kata.available) workspace.append(el("div", "notice", "This kata is planned. Its diagram is a conceptual preview, not captured execution. Running will become available when its README, starter, solution, and tests are added."));
  if (state.active) {const notice = el("div", "notice", "A run is active. "); notice.id = "active-notice"; const active = state.runs.find(r => r.id === state.active); if (active) notice.append(button("Open active run →", "text-button", () => openKata(active.kata_id, active.id))); workspace.append(notice);}
  const summary = el("div", "run-summary"); summary.id = "run-summary"; workspace.append(summary);
  const replay = el("div", "replay-bar"); replay.id = "replay-bar";
  const play = button("▶ Replay", "btn", playReplay); play.id = "play";
  const step = button("Step →", "btn", () => {pause(); setCursor(Math.min(state.cursor + 1, state.events.length));}); step.id = "step";
  const slider = el("input"); slider.id = "cursor"; slider.type = "range"; slider.min = "0"; slider.max = "0"; slider.value = "0"; slider.setAttribute("aria-label", "Replay event position"); slider.addEventListener("input", () => {pause(); setCursor(Number(slider.value));});
  const position = el("span"); position.id = "position";
  replay.append(el("label", "", "RECORDED REPLAY"), play, step, slider, position); workspace.append(replay);
  const grid = el("div", "workspace-grid");
  function panel(title, id, caption) {const panel = el("section", "panel"), header = el("div", "panel-header"); header.append(el("h2", "", title), el("small", "", caption)); panel.append(header); const body = el("div"); body.id = id; panel.append(body); return panel;}
  const explorer = panel("Test explorer", "test-list", "UNITTEST"); explorer.append(el("div", "context-note", "Edit working.py in your IDE. Tests are real; a green result alone does not prove TDD or refactoring."));
  const middle = el("div"), map = panel("Execution map", "flow", "GUIDE + OBSERVATIONS"), timeline = panel("Event timeline", "timeline", "CAPTURED EVENTS"); middle.append(map, timeline); middle.style.display = "grid"; middle.style.gap = "14px";
  grid.append(explorer, middle, panel("Event inspector", "inspector", "SELECT A STEP")); workspace.append(grid); main.append(workspace, guide);
  const previous = runId || state.runs.find(r => r.kata_id === id)?.id;
  if (previous) {await loadRun(previous);} else paint();
}
async function loadRun(runId) {
  const version = state.viewVersion;
  if (state.source) state.source.close(); pause(); state.selected = null;
  try {const data = await api(`/api/runs/${runId}`); if (version !== state.viewVersion) return; state.runId = runId; state.events = data.events; state.cursor = data.events.length; const first = data.events[0]; state.target = first.target; $("#target").value = first.target; state.mode = data.events.at(-1)?.kind === "run_finished" ? "recorded" : "live"; paint(); if (state.mode === "live") subscribe(runId, state.events.length);} catch (error) {toast(error.message);}
}
async function startRun() {
  if (state.launching) return;
  state.launching = true;
  const version = state.viewVersion;
  $("#run-button").disabled = true;
  try {
    const response = await api("/api/runs", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({kata_id: state.kata.id, target: state.target})});
    if (version !== state.viewVersion) {await refresh(); return;}
    cleanup(); state.runId = response.run_id; state.events = []; state.cursor = 0; state.mode = "live"; state.active = response.run_id; paint(); subscribe(response.run_id, 0);
  } catch (error) {toast(error.message);}
  finally {state.launching = false; if (version === state.viewVersion) paint();}
}
function subscribe(runId, after) {
  const stream = new EventSource(`/api/runs/${runId}/events?after=${after}`); state.source = stream;
  stream.onmessage = (message) => {
    if (state.runId !== runId) {stream.close(); return;}
    const event = JSON.parse(message.data); if (state.events.some(e => e.seq === event.seq)) return;
    state.events.push(event); state.cursor = state.events.length;
    if (event.kind === "run_finished") {stream.close(); state.source = null; state.active = null; state.mode = "recorded"; refresh().catch(error => toast(error.message));}
    clearTimeout(paintTimer); paintTimer = setTimeout(paint, 45);
  };
  stream.onerror = () => {if (state.source === stream) toast("Stream disconnected. Reconnecting by event ID; the run will not be rerun.");};
}
function pause() {if (state.playback) clearInterval(state.playback); state.playback = null; if ($("#play")) $("#play").textContent = "▶ Replay";}
function setCursor(value) {state.mode = "replay"; state.cursor = value; state.selected = null; paint();}
function playReplay() {
  if (state.playback) {pause(); return;}
  if (!state.events.length || state.events.at(-1)?.kind !== "run_finished") return;
  state.mode = "replay"; if (state.cursor >= state.events.length) state.cursor = 0;
  $("#play").textContent = "Ⅱ Pause";
  state.playback = setInterval(() => {state.cursor = Math.min(state.events.length, state.cursor + 1); state.selected = null; paint(); if (state.cursor >= state.events.length) pause();}, 180);
}
function paint() {
  if (!$("#workspace")) return;
  const events = state.events.slice(0, state.cursor), final = events.findLast(e => e.kind === "run_finished"), suite = events.find(e => e.kind === "suite_loaded");
  const finished = events.filter(e => e.kind === "test_finished"), passed = finished.filter(e => e.status === "passed").length, failed = finished.filter(e => ["failed", "error"].includes(e.status)).length;
  const summary = $("#run-summary"); summary.replaceChildren(pill(state.mode === "replay" ? "Replay" : final?.status || (state.events.length ? "Running" : "Not run"), state.mode === "replay" ? "" : final?.status || ""), el("span", "", `${passed} passed`), el("span", "", `${failed} failed / error`), el("span", "", `${finished.length} / ${suite?.total ?? "—"} tests`));
  summary.append(el("span", "summary-caption", final?.reason || (state.runId ? `${state.events[0]?.target || state.target} · ${state.runId.slice(0, 8)} · ${state.events.length} recorded events` : "Run a suite to see genuine test events.")));
  const running = state.events.length > 0 && state.events.at(-1).kind !== "run_finished";
  $("#run-button").disabled = !state.kata.available || Boolean(state.active) || running || state.launching;
  $("#target").disabled = !state.kata.available || running;
  $("#play").disabled = !state.events.length || running; $("#step").disabled = !state.events.length || running; $("#cursor").disabled = !state.events.length || running;
  $("#cursor").max = String(state.events.length); $("#cursor").value = String(state.cursor); $("#position").textContent = `${state.cursor} / ${state.events.length}`;
  const tests = new Map();
  events.forEach(e => {if (e.kind === "test_started") tests.set(e.test_id, {start: e, status: "running"}); if (e.kind === "test_finished") tests.set(e.test_id, {...tests.get(e.test_id), end: e, status: e.status});});
  const list = $("#test-list"); list.className = "test-list"; list.replaceChildren();
  if (!tests.size) list.append(el("div", "empty", "Your test suite will appear here. Run the reference solution to explore, or choose the starter to begin with failing tests."));
  tests.forEach((test, id) => {const event = test.end || test.start; const row = button("", `test-item ${state.selected?.test_id === id ? "selected" : ""}`, () => {state.selected = event; paint();}); row.append(el("span", `verdict ${test.status}`, test.status === "passed" ? "✓" : test.status === "running" ? "◌" : test.status === "skipped" ? "−" : "×"), el("span", "", (test.start?.label || id.split(".").at(-1)).replace(/^test_/, "").replaceAll("_", " "))); list.append(row);});
  const traces = events.filter(e => e.kind === "trace"), lastTrace = traces.at(-1), flow = $("#flow"); flow.className = "flow-canvas"; flow.replaceChildren(el("div", "map-note", "CONCEPTUAL ORDER · NOT A CALL GRAPH\nBADGES SHOW OBSERVED FUNCTION CALLS"));
  (state.events[0]?.stages || state.kata.stages).forEach((stage, index) => {const count = traces.filter(e => e.stage === stage.id && e.action === "call").length; const node = el("div", `stage ${count ? "observed" : ""} ${lastTrace?.stage === stage.id ? "last" : ""}`), title = el("div", "stage-title"); title.append(el("h3", "", stage.label), el("span", "", count ? `${count} calls` : "not observed")); node.append(title, el("p", "", stage.functions.length ? stage.functions.map(name => name + "()").join(" · ") : "Design guide · no trace hook")); flow.append(node); if (index < (state.events[0]?.stages || state.kata.stages).length - 1) flow.append(el("div", "connector", "↓"));});
  const legend = el("div", "map-legend"), observed = el("span"), unobserved = el("span"); observed.append(el("i"), "Observed"); unobserved.append(el("i", "grey"), "Guide only"); legend.append(observed, unobserved); flow.append(legend);
  const timeline = $("#timeline"); timeline.className = "event-list"; timeline.replaceChildren();
  if (!events.length) timeline.append(el("div", "empty", "No events captured yet. Live results and replay use the same saved event log."));
  events.slice(-100).reverse().forEach(event => {const row = button("", `event-item ${state.selected?.seq === event.seq ? "selected" : ""}`, () => {state.selected = event; paint();}); const description = el("div", "", event.function ? `${event.function}() · ${event.action}` : event.kind.replaceAll("_", " ")); description.append(el("small", "", event.status || event.label?.replaceAll("_", " ") || (event.test_id ? event.test_id.split(".").at(-1) : new Date(event.at).toLocaleTimeString()))); row.append(el("span", "", String(event.seq).padStart(3, "0")), description); timeline.append(row);});
  const inspector = $("#inspector"); inspector.className = "inspector"; inspector.replaceChildren();
  const selected = state.selected || events.at(-1);
  if (!selected) {inspector.append(el("div", "empty", "Select a test or captured event. Inspect its source location, outcome, or failure details. Arguments, return values, and local variables are not recorded.")); return;}
  inspector.append(el("h3", "", `EVENT ${String(selected.seq).padStart(3, "0")} / ${selected.kind.toUpperCase()}`));
  const dl = el("dl"); [["Function", selected.function], ["Test", selected.test_id], ["Source", selected.file ? `${selected.file}:${selected.line}` : null], ["Status", selected.status], ["Duration", selected.duration_ms !== undefined ? `${selected.duration_ms} ms` : null], ["Return type", selected.result_type], ["Message", selected.message || selected.reason]].forEach(([label, value]) => {if (value !== undefined && value !== null && value !== "") dl.append(el("dt", "", label), el("dd", "", String(value)));}); inspector.append(dl);
  if (selected.details) inspector.append(el("pre", "", selected.details));
  if (selected.kind === "trace") inspector.append(el("p", "context-note", "Captured from Python execution in the selected target. Function events do not prove every conceptual stage or business outcome. Values and locals are intentionally omitted."));
  inspector.append(el("pre", "", JSON.stringify(selected, null, 2)));
}
async function history() {
  const version = ++state.viewVersion;
  cleanup(); state.kata = null; state.tab = "history";
  try {await refresh();} catch (error) {toast(error.message); return;}
  if (version !== state.viewVersion) return;
  nav(); $("#breadcrumb").textContent = "Run history"; const main = $("#main"); main.replaceChildren(el("div", "eyebrow", "LOCAL EVENT ARCHIVE"), el("h1", "", "Every run tells a story."), el("p", "notice", "Reopen a saved run to replay its real events. Replaying never executes tests or calls a model. History is local to this checkout."));
  const list = el("div", "history-list");
  if (!state.runs.length) list.append(el("div", "empty", "No runs yet. Open an available kata and run its tests."));
  state.runs.forEach(run => {const row = el("article", "history-row"), info = el("div"); info.append(el("b", "", state.katas.find(k => k.id === run.kata_id)?.title || run.kata_id), el("small", "", `${run.target} · ${run.id.slice(0, 8)} · ${run.counts.passed || 0} passed`)); const date = el("time", "", new Date(run.started_at).toLocaleString()); date.dateTime = run.started_at; row.append(info, pill(run.status, run.status), date, button(run.status === "running" ? "Follow live ↗" : "Open replay ↗", "text-button", () => openKata(run.kata_id, run.id))); list.append(row);}); main.append(list);
}
$("#home-nav").addEventListener("click", home); $("#history-nav").addEventListener("click", history); $(".brand").addEventListener("click", event => {event.preventDefault(); home();});
home().catch(error => toast(error.message));

// If the learner leaves a live run, release stale controls after its completion.
setInterval(async () => {
  if (!state.active || state.source) return;
  try {
    await refresh();
    if (!state.active && document.querySelector("#workspace")) {
      document.querySelector("#active-notice")?.remove();
      paint();
    }
  } catch (_) { /* A user action or SSE reconnect will surface connection errors. */ }
}, 2000);
