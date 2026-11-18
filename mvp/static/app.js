import { Recorder } from "./recorder.js";

const $ = (id) => document.getElementById(id);
const fragment = new URLSearchParams(location.hash.slice(1));
const token = fragment.get("t") || "";
const recorder = new Recorder();
const UNIT_NAMES = { inches_wc: "in. w.c.", inch_pounds: "in-lb", microfarads: "µF", microamps: "µA",
  millivolts: "mV", megohms: "MΩ", kilohms: "kΩ", degrees: "°F", percent: "%" };
const MAX_SECONDS = 25;
const CHECK_LOCK_MS = 600; // a second tap meant for one value cannot confirm the next
const ORIGINS = { unconfirmed: "Not confirmed. The recording is kept.", skipped: "Skipped",
  technician_typed: "You typed it", checker: "Accepted from your recording without a question",
  corrected: "You corrected it", confirmed: "You confirmed it" };
let state = null;
let lastSaid = "";
let speak = true; // set in init: saved choice, else off in evaluation runs
let busy = false;
let evaluation = false;
let player = null; // the recording playing at read-back, if any
let playRun = 0;
let playing = false;
let pressedAt = 0;
let toggleMode = false;
let chosenSlot = null; // a missing reading picked at the end of the visit

const unitName = (u) => UNIT_NAMES[u] || u;
const show = (id, on) => ($(id).hidden = !on);

function message(text) {
  $("message").textContent = text || "";
  show("message", Boolean(text));
}

async function api(method, path, body, type = "application/json") {
  for (let attempt = 0; ; attempt++) {
    let res;
    try {
      res = await fetch(path, {
        method,
        headers: { "X-Token": token, ...(body ? { "Content-Type": type } : {}) },
        body: body && type === "application/json" ? JSON.stringify(body) : body,
      });
    } catch (err) {
      if (attempt === 2) throw new Error("Can't reach the server. Check the Mac is on and try again.");
      await new Promise((r) => setTimeout(r, 600 * 2 ** attempt)); // same utterance id, so a retry is safe
      continue;
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || res.statusText);
    return data;
  }
}

function micError(err) {
  if (err.message === "insecure") return "The microphone only works on a secure page. Use the https address the server printed.";
  if (err.message === "unsupported") return "This browser can't record audio. Use Safari or Chrome.";
  if (err.name === "NotAllowedError")
    return "Microphone access is blocked. On iPhone: Settings, Apps, Safari, Microphone, Allow. Then reload this page.";
  if (err.name === "NotFoundError") return "No microphone found.";
  return `Microphone problem: ${err.message}`;
}

async function ensureMic() {
  if (recorder.ready) return true;
  try {
    await recorder.init();
    return true;
  } catch (err) {
    message(micError(err));
    return false;
  }
}

function say(text, shown = text) {
  $("say").textContent = shown;
  if (!speak || text === lastSaid || !window.speechSynthesis) return;
  speechSynthesis.cancel();
  speechSynthesis.speak(new SpeechSynthesisUtterance(text));
  lastSaid = text;
}

function currentSlot() {
  const p = state.prompt;
  return p.slot || chosenSlot;
}

function slotItem(s, current) {
  const li = document.createElement("li");
  if (s.key === current) li.className = "current";
  const value = s.value ? `${s.value.replace("/", " / ")} ${unitName(s.unit)}` : "—";
  li.innerHTML = `<span>${s.label}</span><span><span class="value"></span> <span class="status ${s.status}">${s.status}</span></span>`;
  li.querySelector(".value").textContent = value;
  return li;
}

function render() {
  const p = state.prompt;
  $("job").textContent = state.job.title;
  const checking = p.expect === "readback";
  say(p.say, checking ? "Is this value right?" : p.say);
  const capturing = ["reading", "value", "yesno"].includes(p.expect) || (p.expect === "missing" && chosenSlot);
  show("capture", capturing);
  show("yesno", p.expect === "yesno");
  show("missing", p.expect === "missing" && !chosenSlot);
  show("readback", p.expect === "readback");
  show("done", p.expect === "done");
  show("finish", p.expect === "reading");
  show("typed", false);
  $("slots").replaceChildren(...state.slots.map((s) => slotItem(s, currentSlot())));
  if (p.expect === "missing") renderMissing(p.missing);
  if (checking) renderCheck(p);
  $("heard").textContent = state.heard && !checking && p.expect !== "done" ? `Heard: "${state.heard}"` : "";
  const listed = !checking && !(evaluation && p.expect === "done"); // after an evaluation visit, no value is shown
  show("slotsHeading", listed);
  show("slots", listed);
  show("showRecord", !evaluation);
}

function renderMissing(keys) {
  $("missingList").replaceChildren(
    ...keys.map((key) => {
      const li = document.createElement("li");
      li.textContent = state.slots.find((s) => s.key === key).label;
      const record = button("Record", () => {
        chosenSlot = key;
        render();
        say(`${li.firstChild.textContent}.`);
      });
      li.append(record);
      return li;
    }),
  );
}

function renderCheck(p) {
  const it = p.item;
  $("progress").textContent = `Value ${p.position} of ${p.total}`;
  $("checkLabel").textContent = it.label;
  $("checkValue").textContent = it.value ? `${it.value.replace("/", " / ")} ${unitName(it.unit)}` : "No value";
  const unset = it.status === "unconfirmed" || it.status === "skipped";
  $("checkOrigin").textContent = ORIGINS[unset ? it.status : it.by] || ORIGINS[it.status] || "";
  $("checkOk").textContent = it.value ? "Confirm" : "Leave empty";
  $("checkFix").textContent = it.value ? "Correct" : "Record it now";
  show("play", p.clips.length > 0);
  stopPlayback();
  for (const id of ["checkOk", "checkFix"]) {
    $(id).disabled = true;
    setTimeout(() => ($(id).disabled = false), CHECK_LOCK_MS);
  }
}

function stopPlayback() {
  playRun++; // also stops a clip that is still loading
  if (player) player.pause();
}

async function playClip(sha, run, onStart) {
  const res = await fetch(`/api/visits/${state.visit_id}/clips/${sha}`, { headers: { "X-Token": token } });
  if (!res.ok) throw new Error("This recording could not be loaded.");
  const url = URL.createObjectURL(await res.blob());
  try {
    if (run !== playRun) return;
    const audio = (player = new Audio(url));
    const ended = new Promise((resolve, reject) => {
      audio.onended = audio.onpause = resolve;
      audio.onerror = () => reject(new Error("This recording could not be played."));
    });
    await audio.play();
    onStart();
    await ended;
  } finally {
    URL.revokeObjectURL(url);
    player = null;
  }
}

async function playRecordings() {
  if (playing) return;
  playing = true;
  const run = ++playRun;
  const { item, clips } = state.prompt;
  let logged = false;
  const logPlayed = () => {
    if (!logged) api("POST", `/api/visits/${state.visit_id}/tap`, { action: "played", slot: item.slot }).catch(() => {});
    logged = true; // logged once audio actually started
  };
  try {
    for (const sha of clips) {
      if (run !== playRun) break;
      await playClip(sha, run, logPlayed);
    }
  } catch (err) {
    if (err.name !== "AbortError") message(err.message); // AbortError: stopped because the value changed
  } finally {
    playing = false;
  }
}

function button(label, onClick) {
  const b = document.createElement("button");
  b.type = "button";
  b.textContent = label;
  b.onclick = onClick;
  return b;
}

async function refresh() {
  // after a failed request the page may be out of step with the server: redraw from the server's state
  try {
    state = await api("GET", `/api/visits/${state.visit_id}`);
    chosenSlot = null;
    render();
  } catch {
    // keep the error message already shown
  }
}

async function tap(action, slot = "", extra = {}) {
  if (busy) return;
  busy = true;
  try {
    state = await api("POST", `/api/visits/${state.visit_id}/tap`, { action, slot, ...extra });
    chosenSlot = null;
    message("");
    render();
  } catch (err) {
    message(err.message);
    await refresh();
  } finally {
    busy = false;
  }
}

function setTalk(mode) {
  const talk = $("talk");
  talk.classList.toggle("recording", mode !== "idle");
  const labels = { idle: ["Hold to talk", "or tap to start, tap to stop"], hold: ["Listening…", "release when done"],
    toggle: ["Listening…", "tap to stop"], busy: ["Checking…", ""] };
  talk.firstChild.textContent = labels[mode][0];
  talk.querySelector("span").textContent = labels[mode][1];
  talk.disabled = mode === "busy";
}

async function startRecording() {
  if (busy || recorder.recording) return;
  if (window.speechSynthesis) speechSynthesis.cancel(); // never record the app's own voice
  if (!(await ensureMic())) return;
  message("");
  await recorder.start();
  pressedAt = performance.now();
  toggleMode = false;
  setTalk("hold");
  setTimeout(() => recorder.recording && recorder.seconds() >= MAX_SECONDS && stopRecording(), MAX_SECONDS * 1000);
}

async function interrupt(reason) {
  if (!recorder.recording || recorder.stopping) return;
  recorder.cancel();
  setTalk("idle");
  message(`Recording stopped (${reason}). Nothing was saved. Try again.`);
  await api("POST", `/api/visits/${state.visit_id}/tap`, { action: "interrupted", slot: currentSlot(), value: reason })
    .catch(() => {});
}

async function stopRecording() {
  if (!recorder.recording || recorder.stopping) return;
  if (recorder.seconds() < 0.5) return interrupt("too short: hold while you speak, or tap once to start");
  busy = true;
  setTalk("busy");
  const slot = currentSlot();
  try {
    const wav = await recorder.stop();
    const utt = crypto.randomUUID();
    const path = `/api/visits/${state.visit_id}/audio?slot=${encodeURIComponent(slot)}&utt=${utt}`;
    state = await api("POST", path, wav, "audio/wav");
    chosenSlot = null;
    render();
  } catch (err) {
    message(err.message);
    await refresh();
  } finally {
    busy = false;
    setTalk("idle");
  }
}

function wireTalk() {
  const talk = $("talk");
  talk.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    try {
      talk.setPointerCapture(e.pointerId); // releasing off the button still ends the recording
    } catch {
      // a synthetic or already-ended pointer cannot be captured; recording still works
    }
    if (recorder.recording && toggleMode) stopRecording();
    else startRecording();
  });
  talk.addEventListener("pointerup", () => {
    if (!recorder.recording || toggleMode) return;
    if (performance.now() - pressedAt < 350) {
      toggleMode = true; // a quick tap: keep listening until the next tap
      setTalk("toggle");
    } else stopRecording();
  });
  talk.addEventListener("pointercancel", () => interrupt("touch cancelled"));
  talk.addEventListener("contextmenu", (e) => e.preventDefault());
  document.addEventListener("visibilitychange", () => document.hidden && interrupt("the app went to the background"));
  document.addEventListener("keydown", (e) => {
    if (e.code === "Space" && !e.repeat && !$("capture").hidden && document.activeElement.tagName !== "INPUT") {
      e.preventDefault();
      startRecording();
    }
  });
  document.addEventListener("keyup", (e) => e.code === "Space" && !toggleMode && stopRecording());
}

function wireControls() {
  $("yes").onclick = () => tap("yes");
  $("no").onclick = () => tap("no");
  $("skip").onclick = () => tap("skip", currentSlot());
  $("finish").onclick = () => tap("finish");
  $("skipMissing").onclick = () => tap("skip_missing");
  $("checkOk").onclick = () => tap("confirm", state.prompt.item.slot);
  $("checkFix").onclick = () => tap("fix", state.prompt.item.slot);
  $("play").onclick = playRecordings;
  $("again").onclick = () => {
    history.replaceState(null, "", `#t=${token}`);
    location.reload();
  };
  $("voice").onclick = () => {
    setSpeak(!speak);
    try {
      localStorage.setItem("spokenPrompts", String(speak));
    } catch {
      // private mode: the choice lasts until the page reloads
    }
    if (!speak && window.speechSynthesis) speechSynthesis.cancel();
  };
  $("typeToggle").onclick = () => {
    const slot = state.slots.find((s) => s.key === currentSlot());
    $("typedUnit").replaceChildren(...slot.units.map((u) => new Option(unitName(u), u)));
    show("typed", true);
    $("typedValue").focus();
  };
  $("typed").onsubmit = (e) => {
    e.preventDefault();
    tap("typed", currentSlot(), { value: $("typedValue").value, unit: $("typedUnit").value });
    $("typedValue").value = "";
  };
  $("showRecord").onclick = async () => {
    const record = await api("GET", `/api/visits/${state.visit_id}/record`);
    $("record").textContent = JSON.stringify(record, null, 2);
    show("record", true);
  };
}

function openVisit() {
  show("start", false);
  show("visit", true);
  render();
}

async function begin() {
  if (!(await ensureMic())) return; // ask for the microphone during this tap: iPhone needs a user gesture
  try {
    state = await api("POST", "/api/visits", { job: $("jobs").value });
    history.replaceState(null, "", `#t=${token}&v=${state.visit_id}`); // a reload resumes this visit
    openVisit();
  } catch (err) {
    message(err.message);
  }
}

function setSpeak(on) {
  speak = on;
  $("voice").setAttribute("aria-pressed", String(on));
  $("voice").textContent = `Spoken prompts: ${on ? "on" : "off"}`;
}

function savedSpeak() {
  try {
    return localStorage.getItem("spokenPrompts");
  } catch {
    return null;
  }
}

async function init() {
  wireTalk();
  wireControls();
  if (!token) return message("Open the full address the server printed (it ends with #t=…).");
  try {
    let jobs;
    ({ jobs, evaluation } = await api("GET", "/api/jobs"));
    $("jobs").replaceChildren(...jobs.map((j) => new Option(j.title, j.id)));
    show("evalnote", evaluation);
    const saved = savedSpeak();
    setSpeak(saved === null ? !evaluation : saved === "true");
    $("begin").onclick = begin;
    if (fragment.get("v")) {
      state = await api("GET", `/api/visits/${fragment.get("v")}`);
      openVisit();
    }
  } catch (err) {
    message(err.message);
  }
  if (new URLSearchParams(location.search).has("selftest")) import("./selftest.js").then((m) => m.run());
}

init();
