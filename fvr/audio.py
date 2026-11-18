"""Text-to-speech for synthetic lines (macOS `say`) and seeded noise mixing at a target SNR."""

import random
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 16000


def tts(text: str, voice: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["say", "-v", voice, "-o", str(out), "--file-format=WAVE", "--data-format=LEI16@16000", text], check=True
    )


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x**2)) + 1e-12)


def mix(speech_path: Path, noise_path: Path, snr_db: float, seed: int, out: Path) -> None:
    """Add a seeded random slice of noise scaled so speech RMS / noise RMS equals `snr_db`."""
    speech, sr = sf.read(speech_path, dtype="float32")
    noise, nsr = sf.read(noise_path, dtype="float32")
    if speech.ndim > 1:
        speech = speech.mean(axis=1)
    if noise.ndim > 1:
        noise = noise.mean(axis=1)
    if sr != SR or nsr != SR:
        raise ValueError(f"expected {SR} Hz audio, got {sr} and {nsr}")
    rng = random.Random(seed)
    while len(noise) < len(speech):
        noise = np.concatenate([noise, noise])
    start = rng.randrange(0, len(noise) - len(speech) + 1)
    segment = noise[start : start + len(speech)]
    scale = _rms(speech) / (_rms(segment) * 10 ** (snr_db / 20))
    mixed = speech + scale * segment
    peak = np.max(np.abs(mixed))
    if peak > 0.99:
        mixed = mixed * (0.99 / peak)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, mixed, SR, subtype="PCM_16")
