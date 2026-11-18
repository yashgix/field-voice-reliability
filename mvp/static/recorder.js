// Microphone capture as 16-bit PCM WAV at the device's own rate. WAV avoids the codec differences between Safari
// (AAC in MP4) and Chrome (Opus in WebM); the server resamples.
export class Recorder {
  // Live mode turns on echo cancellation (the page speaks) and reads every block through `onchunk`.
  async init({ echoCancellation = false } = {}) {
    if (!window.isSecureContext) throw new Error("insecure");
    if (!navigator.mediaDevices?.getUserMedia) throw new Error("unsupported");
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation, noiseSuppression: false, autoGainControl: true },
    });
    if (this.ctx) this.ctx.close(); // a microphone that was lost is opened again
    this.lost = false;
    this.ctx = new AudioContext();
    await this.ctx.audioWorklet.addModule("worklet.js");
    const source = this.ctx.createMediaStreamSource(this.stream);
    const node = new AudioWorkletNode(this.ctx, "capture");
    const mute = this.ctx.createGain();
    mute.gain.value = 0; // the worklet must be connected to run; nothing is played back
    source.connect(node).connect(mute).connect(this.ctx.destination);
    node.port.onmessage = (e) => {
      this.onchunk?.(e.data);
      if (this.recording) this.chunks.push(e.data);
    };
    this.stream.getAudioTracks()[0].onended = () => (this.lost = true);
  }

  get ready() {
    return Boolean(this.ctx) && !this.lost;
  }

  async start() {
    await this.ctx.resume();
    this.chunks = [];
    this.recording = true;
    this.startedAt = performance.now();
  }

  seconds() {
    return this.recording ? (performance.now() - this.startedAt) / 1000 : 0;
  }

  cancel() {
    this.recording = false;
    this.chunks = [];
  }

  async stop() {
    this.stopping = true; // from here an interruption can no longer discard the clip
    await new Promise((r) => setTimeout(r, 200)); // keep the end of the last word
    this.recording = false;
    this.stopping = false;
    return encodeWav(this.chunks, this.ctx.sampleRate);
  }
}

export function encodeWav(chunks, rate) {
  const frames = chunks.reduce((n, c) => n + c.length, 0);
  const view = new DataView(new ArrayBuffer(44 + frames * 2));
  const text = (at, s) => [...s].forEach((ch, i) => view.setUint8(at + i, ch.charCodeAt(0)));
  text(0, "RIFF");
  view.setUint32(4, 36 + frames * 2, true);
  text(8, "WAVEfmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, rate, true);
  view.setUint32(28, rate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  text(36, "data");
  view.setUint32(40, frames * 2, true);
  let at = 44;
  for (const chunk of chunks) {
    for (const x of chunk) {
      view.setInt16(at, Math.max(-1, Math.min(1, x)) * 0x7fff, true);
      at += 2;
    }
  }
  return new Blob([view], { type: "audio/wav" });
}
