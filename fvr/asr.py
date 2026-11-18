"""Local Whisper decoding: MLX on Apple Silicon, faster-whisper (CTranslate2) everywhere else.

The engine is imported on first use, so importing this module stays light. MLX streams belong to the thread that
imports MLX, so a server calls `load_engine()` on its main thread before any worker decodes.
"""

import platform
import sys
import time
from dataclasses import dataclass
from functools import cache

APPLE_SILICON = sys.platform == "darwin" and platform.machine() == "arm64"
MODEL = "mlx-community/whisper-large-v3-turbo"
FASTER_MODEL = "large-v3-turbo"
DECODE = {
    "language": "en",
    "temperature": (0.0,),
    "condition_on_previous_text": False,
    "word_timestamps": True,
    "fp16": True,
}


@dataclass
class Decode:
    text: str
    words: list[tuple[str, float]]
    seconds: float


@cache
def _faster_model():
    from faster_whisper import WhisperModel

    return WhisperModel(FASTER_MODEL, device="auto", compute_type="default")


def load_engine() -> None:
    if APPLE_SILICON:
        import mlx_whisper  # noqa: F401
    else:
        _faster_model()


def _mlx(audio_path: str, prompt: str | None) -> tuple[str, list[tuple[str, float]]]:
    import mlx_whisper

    r = mlx_whisper.transcribe(audio_path, path_or_hf_repo=MODEL, initial_prompt=prompt, **DECODE)
    return r["text"].strip(), [(w["word"], float(w["probability"])) for s in r["segments"] for w in s.get("words", [])]


def _faster(audio_path: str, prompt: str | None) -> tuple[str, list[tuple[str, float]]]:
    segments, _ = _faster_model().transcribe(
        audio_path, language="en", temperature=0.0, condition_on_previous_text=False, word_timestamps=True,
        initial_prompt=prompt,
    )  # fmt: skip
    segments = list(segments)
    words = [(w.word, float(w.probability)) for s in segments for w in s.words or []]
    return " ".join(s.text.strip() for s in segments), words


def transcribe(audio_path: str, prompt: str | None) -> Decode:
    start = time.perf_counter()
    text, words = (_mlx if APPLE_SILICON else _faster)(audio_path, prompt)
    return Decode(text, words, time.perf_counter() - start)
