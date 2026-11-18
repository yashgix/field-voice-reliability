import { Listener } from "./listener.js";
import { Recorder, encodeWav } from "./recorder.js";

const token = new URLSearchParams(location.hash.slice(1)).get("t") ?? "";
const $ = (id) => document.getElementById(id);
const AFTER_SPEECH_S = 0.4;
const UNITS = { psi: "psi", F: "°F", A: "A", uF: "µF", V: "V", in_wc: "in. w.c.", uA: "µA", Mohm: "MΩ" };
const MODES = { calibrating: "Measuring the room, stay quiet", idle: "Listening", speaking: "Hearing you",
  muted: "Speaking", ended: "Visit ended" };

let session, fields = {}, listener, spoken = new Set(), sending = Promise.resolve(), uploads = 0;

async function api(path, options = {}) {
  const res = await fetch(path, { ...options, headers: { "X-Token": token, ...options.headers } });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).error ?? res.statusText);
  return res.headers.get("Content-Type") === "audio/wav" ? res.blob() : res.json();
}

const median = (xs) => [...xs].sort((a, b) => a - b)[Math.floor(xs.length / 2)] ?? 0;

function send(blob) {
  uploads += 1;
  sending = sending
    .then(() => api(`/api/sessions/${session}/audio`, { method: "POST", headers: { "Content-Type": "audio/wav" },
      body: blob }))
    .catch(showError)
    .finally(() => (uploads -= 1));
}

// The page's own sound (a question or a replayed clip) never reaches the record: the listener is muted meanwhile.
function quietly(play, stop) {
  listener.mute();
  let ended = false;
  const done = () => {
    if (ended) return;
    ended = true;
    setTimeout(() => listener.unmute(), AFTER_SPEECH_S * 1000);
  };
  listener.onBarge = () => {
    stop();
    ended = true;
  };
  play(done);
}

function ask(text) {
  const u = new SpeechSynthesisUtterance(text);
  quietly((done) => {
    u.onend = u.onerror = done;
    setTimeout(done, 3000 + text.length * 90); // Chrome sometimes never fires onend
    speechSynthesis.cancel();
    speechSynthesis.speak(u);
  }, () => speechSynthesis.cancel());
}

async function play(clip) {
  const audio = new Audio(URL.createObjectURL(await api(`/api/sessions/${session}/clips/${clip}`)));
  quietly((done) => {
    audio.onended = audio.onerror = done;
    audio.play().catch(done);
  }, () => audio.pause());
}

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

function heardNode(heard) {
  const p = el("span", "said");
  for (const word of heard.split(" ")) {
    p.append(word.startsWith("~") ? el("span", "unsure", word.slice(1)) : word, " ");
  }
  return p;
}

function fieldLabel(name) {
  const base = name.replace(/_after$/, "");
  const label = base.replace(/_(uf|ua)$/, "").replaceAll("_", " ");
  return { label: label + (base === name ? "" : " (after repair)"), unit: UNITS[fields[base]] ?? "" };
}

function evidence(ids, clips) {
  const span = el("span", "evidence");
  for (const id of ids ?? []) {
    const b = el("button", "chip", id.endsWith("q") ? "question" : `line ${id}`);
    if (clips[id]) b.onclick = () => play(clips[id]);
    else b.disabled = true;
    span.append(b);
  }
  return span;
}

function row(label, value, ids, clips, cls = "") {
  const li = el("li", cls);
  li.append(el("span", "label", label), el("strong", "value", value), evidence(ids, clips));
  return li;
}

function renderRecord(state) {
  const rec = state.record ?? { readings: [], work: [], equipment: [] };
  const clips = Object.fromEntries(state.lines.map((l) => [l.id, l.clip]));
  const box = $("record");
  box.replaceChildren();
  const open = (rec.readings ?? []).filter((r) => r.status === "unresolved" || Array.isArray(r.equip));
  if (open.length) {
    const ul = el("ul", "rows open");
    const ids = new Set(state.equipment.map((e) => e.id));
    for (const r of open) {
      const { label, unit } = fieldLabel(r.field);
      const options = (r.options ?? []).map(String);
      const units = options.filter((o) => ids.has(o)); // the model sometimes lists candidate units as options
      const values = options.filter((o) => !ids.has(o)).concat(r.value ? [String(r.value)] : []);
      const where = [...new Set([r.equip, units].flat())].join(" or ");
      const what = [...new Set(values)].map((v) => `${v} ${unit}`).join(" or ") || "value unclear";
      ul.append(row(`${label}, ${where}`, `${what}: not settled, will not guess`, r.evidence, clips, "unsettled"));
    }
    box.append(el("h3", "", "Not settled"), ul);
  }
  for (const e of state.equipment) {
    const ul = el("ul", "rows");
    for (const r of rec.readings ?? []) {
      if (r.equip !== e.id || r.status === "unresolved") continue;
      const { label, unit } = fieldLabel(r.field);
      ul.append(row(label, `${r.value} ${unit}`, r.evidence, clips));
    }
    for (const w of (rec.work ?? []).filter((w) => w.equip === e.id)) {
      ul.append(row(w.task.replaceAll("_", " "), w.status.replace("_", " "), w.evidence, clips, `work ${w.status}`));
    }
    for (const q of (rec.equipment ?? []).filter((q) => q.equip === e.id)) {
      ul.append(row(q.field, q.value, q.evidence, clips));
    }
    const card = el("section", "unit");
    card.append(el("h3", "", `${e.id} · ${e.type.replace("_", " ")} · ${e.location}`),
      el("p", "muted", `${e.make} ${e.model}, serial ${e.serial}`));
    card.append(ul.children.length ? ul : el("p", "muted", "Nothing recorded yet."));
    box.append(card);
  }
}

const STATUS = { queued: "waiting", updating: "updating the record", recorded: "", silent: "no words heard" };

function renderLines(state) {
  const asked = Object.fromEntries(state.questions.map((q) => [q.id.slice(0, -1), q.text]));
  const ol = $("lines");
  ol.replaceChildren();
  for (const l of state.lines) {
    const li = el("li", l.status);
    const replay = el("button", "chip", "▶");
    replay.onclick = () => play(l.clip);
    li.append(el("span", "num", l.id), l.heard ? heardNode(l.heard) : el("span", "muted", "…"), replay);
    if (STATUS[l.status]) li.append(el("span", "tag", STATUS[l.status]));
    else li.append(el("span", "tag", `${(l.recorded_at - l.received).toFixed(1)} s`));
    ol.append(li);
    if (asked[l.id]) ol.append(el("li", "asked", `Asked: ${asked[l.id]}`));
  }
  ol.lastElementChild?.scrollIntoView({ block: "nearest" });
}

function renderStats(state) {
  const times = state.lines.filter((l) => l.recorded_at).map((l) => l.recorded_at - l.received);
  const dollars = state.updates.reduce((s, u) => s + (u.dollars ?? 0), 0);
  const parts = [`${state.lines.length} lines`, `$${dollars.toFixed(3)} spent`];
  if (times.length) parts.splice(1, 0, `record ${median(times).toFixed(1)} s after each sentence (median)`);
  if (state.waiting || uploads) parts.push(`${state.waiting + uploads} waiting`);
  $("stats").textContent = parts.join(" · ");
}

function showError(e) {
  $("error").textContent = String(e.message ?? e);
  $("error").hidden = false;
}

async function poll() {
  try {
    const state = await api(`/api/sessions/${session}`);
    renderRecord(state);
    renderLines(state);
    renderStats(state);
    if (state.error) showError(state.error);
    const q = state.question;
    $("question").hidden = !q;
    if (q) $("question").textContent = `Asked: ${q.text}`;
    if (q && !spoken.has(q.id) && listener.mode === "idle") {
      spoken.add(q.id);
      ask(q.text);
    }
  } catch (e) {
    showError(e);
  }
}

function tick() {
  $("status").textContent = MODES[listener.mode];
  $("status").dataset.mode = listener.mode;
  $("level").style.width = `${Math.min(100, (50 * listener.level) / listener.startBar)}%`;
  requestAnimationFrame(tick);
}

async function start() {
  $("start").disabled = true;
  try {
    const recorder = new Recorder();
    await recorder.init({ echoCancellation: true });
    fields = (await api("/api/fields")).fields;
    session = (await api("/api/sessions", { method: "POST", body: "{}" })).session;
    const rate = recorder.ctx.sampleRate;
    listener = new Listener(rate, (chunks) => send(encodeWav(chunks, rate)));
    recorder.onchunk = (chunk) => listener.push(chunk);
    await recorder.start(); // the whole session is also kept, to check the voice detector against it afterwards
    $("intro").hidden = true;
    $("live").hidden = false;
    $("stop").onclick = async () => {
      listener.mode = "ended";
      $("stop").hidden = true;
      const whole = await recorder.stop();
      recorder.stream.getTracks().forEach((t) => t.stop());
      await sending;
      await api(`/api/sessions/${session}/full`, { method: "POST", headers: { "Content-Type": "audio/wav" },
        body: whole }).catch(showError);
    };
    tick();
    setInterval(poll, 1000);
  } catch (e) {
    $("intro-error").textContent = `Could not start: ${e.message}`;
    $("intro-error").hidden = false;
    $("start").disabled = false;
  }
}

// Watch-only view of an existing session (e.g. a recorded visit played in by live/feed.py): no microphone.
async function watch(id) {
  session = id;
  fields = (await api("/api/fields")).fields;
  listener = { mode: "ended", level: 0, startBar: 1, mute() {}, unmute() {} };
  $("intro").hidden = true;
  $("live").hidden = false;
  $("stop").hidden = true;
  $("status").textContent = "Watching";
  setInterval(poll, 1000);
}

const watched = new URLSearchParams(location.hash.slice(1)).get("s");
if (watched) watch(watched);
$("start").onclick = start;
