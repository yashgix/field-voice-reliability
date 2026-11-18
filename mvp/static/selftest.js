// Browser capture check, loaded only with ?selftest: drives the real buttons, the server records what arrived.
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

export async function run() {
  document.getElementById("begin").click();
  await wait(2000);
  const talk = document.getElementById("talk");
  talk.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true }));
  await wait(4500);
  talk.dispatchEvent(new PointerEvent("pointerup", { bubbles: true }));
}
