import hashlib
import io
import json
import wave
from pathlib import Path

import numpy as np
import pytest

from fvr.asr import Decode
from fvr.readings import Settings
from mvp.engine import Engine
from mvp.events import ClipStore, EventLog

JOBS = Path(__file__).resolve().parents[1] / "mvp/jobs"


def wav(seconds: float = 1.0, amplitude: float = 0.3, salt: str = "", rate: int = 16000) -> bytes:
    """A tone clip; `salt` makes the bytes (and so the clip id) unique per scripted transcript."""
    t = np.arange(int(seconds * rate)) / rate
    tone = amplitude * np.sin(2 * np.pi * (200 + int(hashlib.md5(salt.encode()).hexdigest()[:3], 16)) * t)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(rate)
        w.writeframes((tone * 32767).astype("<i2").tobytes())
    return buf.getvalue()


class FakeASR:
    """Returns the transcript scripted for each clip and records every call."""

    def __init__(self):
        self.script, self.calls = {}, []

    def clip(self, text: str) -> bytes:
        audio = wav(salt=text)
        self.script[hashlib.sha256(audio).hexdigest()] = text
        return audio

    def __call__(self, path: str, prompt: str | None) -> Decode:
        self.calls.append((Path(path).stem, prompt))
        text = self.script[Path(path).stem]
        return Decode(text, [(w, 0.9) for w in text.split()], 0.01)


@pytest.fixture
def asr() -> FakeASR:
    return FakeASR()


@pytest.fixture
def engine(tmp_path, asr) -> Engine:
    log, clips = EventLog(tmp_path / "events.db"), ClipStore(tmp_path / "clips")
    return Engine(log, clips, asr, Settings(min_prob=0.0), {"code": "test", "model": "fake"})


@pytest.fixture
def hvac() -> dict:
    return json.loads((JOBS / "demo-hvac.json").read_text())


@pytest.fixture
def electrical() -> dict:
    return json.loads((JOBS / "demo-electrical.json").read_text())
