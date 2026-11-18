"""Browser capture check on this Mac: headless Chrome with a synthetic voice file as its microphone.

Starts the real server (real Whisper) on localhost, opens the page with ?selftest so it presses the real buttons, and
checks what reached the server: WAV format, length, transcript, the app's decision. Writes results/mvp/browser-check.md.
Usage: PYTHONPATH=. .venv/bin/python scripts/mvp_browser_check.py
"""

import io
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.request
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PHRASE = "Line voltage is two forty one volts."
PORT = 8765


def fake_microphone(folder: Path) -> Path:
    """2.5 s of silence, the phrase, silence. Played once from when the page opens the microphone, about 2 s before
    the self-test starts recording."""
    aiff, out = folder / "phrase.aiff", folder / "mic.wav"
    subprocess.run(["say", "-v", "Samantha", "-o", str(aiff), PHRASE], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(aiff), "-af", "adelay=2500,apad=pad_dur=2",
                    "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(out)], check=True)  # fmt: skip
    return out


def get(path: str, token: str) -> dict:
    req = urllib.request.Request(f"http://localhost:{PORT}{path}", headers={"X-Token": token})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def wait_for_utterance(token: str, timeout: float = 90) -> tuple[str, dict]:
    end = time.time() + timeout
    while time.time() < end:
        visits = get("/api/audit", token)["visits"]
        if visits:
            record = get(f"/api/visits/{visits[0]}/record", token)
            if any(r["evidence"] for r in record["readings"]):
                return visits[0], record
        time.sleep(1)
    raise TimeoutError("no recording reached the server")


def main() -> None:
    env = dict(os.environ, PYTHONPATH=str(ROOT), HF_HUB_OFFLINE="1",
               HF_HOME=str(Path.home() / "field-voice-data/hf"))  # fmt: skip
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        mic = fake_microphone(folder)
        server = subprocess.Popen(
            [str(ROOT / ".venv/bin/python"), "-m", "mvp.server", "--port", str(PORT), "--data", str(folder / "data")],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )  # fmt: skip
        try:
            token = re.search(r"#t=(\S+)", server.stdout.readline()).group(1)
            chrome = subprocess.Popen([
                CHROME, "--headless=new", f"--user-data-dir={folder / 'chrome'}", "--no-first-run",
                "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                f"--use-file-for-fake-audio-capture={mic}%noloop", "--autoplay-policy=no-user-gesture-required",
                "--disable-features=AudioServiceOutOfProcess",  # the sandboxed audio service cannot read the file
                f"http://localhost:{PORT}/?selftest#t={token}",
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # fmt: skip
            try:
                visit_id, record = wait_for_utterance(token)
            finally:
                chrome.kill()
            evidence = record["readings"][0]["evidence"][0]
            clip = (folder / "data/clips" / f"{evidence['clip']}.wav").read_bytes()
            (ROOT / "results/mvp/browser-clip.wav").write_bytes(clip)  # kept so the capture can be listened to
            with wave.open(io.BytesIO(clip)) as w:
                fmt = (w.getframerate(), w.getnchannels(), w.getsampwidth() * 8, w.getnframes() / w.getframerate())
            state = get(f"/api/visits/{visit_id}", token)
        finally:
            server.kill()
    reading = record["readings"][0]
    lines = [
        "# Browser capture check (headless Chrome on this Mac, synthetic voice as the microphone)", "",
        f"Said: \"{PHRASE}\" (macOS `say`, Chrome's fake microphone), by `scripts/mvp_browser_check.py`.",
        "", f"- Clip received: {fmt[0]} Hz, {fmt[1]} channel, {fmt[2]}-bit PCM WAV, {fmt[3]:.1f} s",
        f"- Whisper heard: \"{evidence['transcript']}\" (clip problem: {evidence['problem']})",
        f"- Stored: {reading['label']} = {reading['value']} {reading['unit']} ({reading['status']}, {reading['by']})",
        f"- Next prompt: \"{state['prompt']['say']}\"", f"- Audit: {record['audit']}",
    ]  # fmt: skip
    out = ROOT / "results/mvp/browser-check.md"
    out.write_text("\n".join(lines) + "\n")
    print(out.read_text())


if __name__ == "__main__":
    main()
