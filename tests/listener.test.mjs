import assert from "node:assert/strict";
import { test } from "node:test";

import { Listener } from "../live/static/listener.js";

const RATE = 44100, CHUNK_S = 2048 / RATE;

function feed(listener, level, seconds) {
  for (let i = 0; i < Math.round(seconds / CHUNK_S); i++) listener.push(new Float32Array(2048).fill(level));
}

function listen() {
  const lines = [];
  return { listener: new Listener(RATE, (wav) => lines.push(wav)), lines };
}

test("soft speech is heard once a loud start has settled (first mic session: room 0.035 at first, then 0.006)", () => {
  const { listener, lines } = listen();
  feed(listener, 0.035, 3);
  feed(listener, 0.006, 6);
  feed(listener, 0.05, 1);
  feed(listener, 0.006, 1);
  assert.equal(lines.length, 1);
});

test("a comma pause does not split a sentence once the room is measured right", () => {
  const { listener, lines } = listen();
  feed(listener, 0.006, 3);
  feed(listener, 0.09, 0.8);
  feed(listener, 0.04, 0.5); // quieter words after the comma
  feed(listener, 0.09, 0.8);
  feed(listener, 0.006, 1);
  assert.equal(lines.length, 1);
});

test("silence and a short click send nothing", () => {
  const { listener, lines } = listen();
  feed(listener, 0.006, 3);
  feed(listener, 0.2, 0.15);
  feed(listener, 0.006, 3);
  assert.equal(lines.length, 0);
});

test("the page's own voice is ignored, talking clearly over it stops it", () => {
  const { listener, lines } = listen();
  let barged = 0;
  listener.onBarge = () => (barged += 1);
  feed(listener, 0.006, 3);
  listener.mute();
  feed(listener, 0.05, 2); // speaker leak
  assert.equal(barged, 0);
  feed(listener, 0.2, 1); // the technician, four times the leak
  feed(listener, 0.006, 1);
  assert.equal(barged, 1);
  assert.equal(lines.length, 1);
});

test("a question that starts soft and gets louder is not taken for the technician (second mic session)", () => {
  const { listener, lines } = listen();
  let barged = 0;
  listener.onBarge = () => (barged += 1);
  feed(listener, 0.005, 3);
  listener.mute();
  for (const level of [0.006, 0.017, 0.026, 0.009, 0.021, 0.036, 0.039, 0.022, 0.03, 0.031]) feed(listener, level, 0.3);
  listener.unmute();
  feed(listener, 0.005, 1);
  assert.equal(barged, 0);
  assert.equal(lines.length, 0);
});
