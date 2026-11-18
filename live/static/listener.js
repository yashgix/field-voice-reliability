const CALIBRATE_S = 2;
const END_PAUSE_S = 0.7, MIN_SPEECH_S = 0.3, PREROLL_S = 0.3, MAX_LINE_S = 25, WINDOW_S = 5;
const START_FACTOR = 3, STOP_FACTOR = 2, MIN_LEVEL = 0.002, FLOOR_PERCENTILE = 0.1;
// Talking over the page's voice: clearly louder than what its speaker leaks into the mic (first mic sessions: leak
// 10-39, voice 40-370, room 5, in thousandths), on 3 of the last 5 blocks after the first 0.4 s.
const BARGE_LEAK_FACTOR = 3, BARGE_ROOM_FACTOR = 10, BARGE_SETTLE_S = 0.4;

const rms = (chunk) => Math.sqrt(chunk.reduce((s, x) => s + x * x, 0) / chunk.length);
const percentile = (xs, p) => [...xs].sort((a, b) => a - b)[Math.floor(xs.length * p)] ?? 0;

// Cuts the microphone stream into spoken lines at pauses. The room level is the quietest tenth of the last 5 s, so it
// follows the microphone's gain settling and noise coming and going. While the page itself makes sound the room level
// is frozen and it only listens for the technician talking over it.
export class Listener {
  constructor(rate, onLine) {
    Object.assign(this, { rate, onLine, chunkS: 2048 / rate, mode: "calibrating", recent: [], pre: [], line: [] });
    Object.assign(this, { loud: 0, level: 0, floor: MIN_LEVEL });
  }

  get startBar() {
    return this.floor * START_FACTOR;
  }

  push(chunk) {
    this.level = rms(chunk);
    if (this.mode === "ended") return;
    if (this.mode !== "muted") this.track();
    if (this.mode === "calibrating") {
      if (this.recent.length * this.chunkS >= CALIBRATE_S) this.mode = "idle";
      return;
    }
    if (this.mode === "speaking") return this.extend(chunk);
    this.pre.push(chunk);
    if (this.pre.length * this.chunkS > PREROLL_S) this.pre.shift();
    if (this.mode === "muted") return this.overheard();
    this.loud = this.level > this.startBar ? this.loud + 1 : 0;
    if (this.loud >= 2) this.begin();
  }

  overheard() {
    const settled = this.leak.length * this.chunkS >= BARGE_SETTLE_S;
    const bar = Math.max(this.floor * BARGE_ROOM_FACTOR, percentile(this.leak, 0.9) * BARGE_LEAK_FACTOR);
    this.over = [...this.over.slice(-4), settled && this.level > bar];
    this.leak.push(this.level);
    if (this.over.filter(Boolean).length >= 3) {
      this.loud = 3;
      this.begin();
    }
  }

  track() {
    this.recent.push(this.level);
    if (this.recent.length * this.chunkS > WINDOW_S) this.recent.shift();
    this.floor = Math.max(percentile(this.recent, FLOOR_PERCENTILE), MIN_LEVEL);
  }

  begin() {
    if (this.mode === "muted") this.onBarge?.();
    Object.assign(this, { mode: "speaking", line: this.pre, pre: [], quiet: 0, voiced: this.loud, loud: 0 });
  }

  extend(chunk) {
    this.line.push(chunk);
    if (this.level > this.floor * STOP_FACTOR) [this.quiet, this.voiced] = [0, this.voiced + 1];
    else this.quiet += 1;
    if (this.quiet * this.chunkS >= END_PAUSE_S || this.line.length * this.chunkS >= MAX_LINE_S) this.finish();
  }

  finish() {
    const tail = Math.max(0, this.quiet - Math.round(0.2 / this.chunkS)); // keep 0.2 s after the last word
    const chunks = this.line.slice(0, this.line.length - tail);
    if (this.voiced * this.chunkS >= MIN_SPEECH_S) this.onLine(chunks);
    Object.assign(this, { mode: "idle", line: [], loud: 0 });
  }

  mute() {
    Object.assign(this, { mode: "muted", leak: [], over: [], loud: 0 });
  }

  unmute() {
    if (this.mode === "muted") Object.assign(this, { mode: "idle", pre: [], loud: 0 });
  }
}
