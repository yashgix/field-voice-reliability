"""A real recording of a visit script: cut one take into its lines, one WAV per line.

Usage: python -m live.voice TAKE.wav VISIT.json FIRST LAST OUT_DIR [--align]
       python -m live.voice --recognise VISIT.json LINES_DIR REPLIES_DIR OUT.json
FIRST and LAST are the script's line ids the take covers. Headset lines are skipped. By default the take is cut at
the pauses, and the number of pieces must equal the number of spoken lines. With --align (for takes where noise fills
the pauses), Whisper transcribes the whole take with word timings, the words are lined up with the script's words,
and each line is cut where its own words are.
"""

import argparse
import re
from difflib import SequenceMatcher
from pathlib import Path

import mlx_whisper
import numpy as np
import soundfile as sf

from fvr.asr import DECODE, MODEL
from live.scenario import load

FRAME_S = 0.03
MIN_PAUSE_S = 0.6
MIN_SPEECH_S = 0.25


def frame_levels(audio: np.ndarray, rate: int) -> np.ndarray:
    n = int(FRAME_S * rate)
    frames = audio[: len(audio) // n * n].reshape(-1, n)
    return np.sqrt((frames**2).mean(axis=1) + 1e-12)


def speech_spans(audio: np.ndarray, rate: int, threshold: float) -> list[tuple[int, int]]:
    """Sample ranges of speech, split where the level stays under `threshold` for at least MIN_PAUSE_S."""
    loud = frame_levels(audio, rate) > threshold
    n, spans, start, quiet = int(FRAME_S * rate), [], None, 0
    for i, on in enumerate(loud):
        if on:
            start = i if start is None else start
            quiet = 0
        elif start is not None:
            quiet += 1
            if quiet * FRAME_S >= MIN_PAUSE_S:
                spans.append((start, i - quiet + 1))
                start, quiet = None, 0
    if start is not None:
        spans.append((start, len(loud)))
    return [(a * n, b * n) for a, b in spans if (b - a) * FRAME_S >= MIN_SPEECH_S]


def cut(audio: np.ndarray, rate: int, pieces: int) -> list[tuple[int, int]] | None:
    """Try thresholds between the noise floor and the speech level until the take splits into `pieces`."""
    levels = frame_levels(audio, rate)
    floor, speech = np.percentile(levels, 10), np.percentile(levels, 90)
    for weight in np.linspace(0.05, 0.6, 56):
        spans = speech_spans(audio, rate, floor + weight * (speech - floor))
        if len(spans) == pieces:
            return spans
    return None


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def timed_words(path: Path) -> list[tuple[str, float, float]]:
    result = mlx_whisper.transcribe(str(path), path_or_hf_repo=MODEL, **DECODE)
    return [(w["word"], w["start"], w["end"]) for seg in result["segments"] for w in seg.get("words", [])]


def align(texts: list[str], words: list[tuple[str, float, float]], rate: int) -> list[tuple[int, int]]:
    """Each script line's span in the take: from its first to its last word that lines up with the transcript.
    A line with no matching word gets the gap between its neighbours."""
    script = [(i, w) for i, text in enumerate(texts) for w in _words(text)]
    heard = [(w, start, end) for word, start, end in words for w in _words(word)]
    matcher = SequenceMatcher(None, [w for _, w in script], [w for w, _, _ in heard], autojunk=False)
    times: dict[int, list[tuple[float, float]]] = {}
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            line = script[block.a + k][0]
            times.setdefault(line, []).append(heard[block.b + k][1:])
    spans = []
    for i in range(len(texts)):
        if i in times:
            spans.append((min(s for s, _ in times[i]), max(e for _, e in times[i])))
        else:
            before = spans[-1][1] if spans else 0.0
            after = next((min(s for s, _ in times[j]) for j in range(i + 1, len(texts)) if j in times), before + 2)
            spans.append((before, after))
    return [(int(s * rate), int(e * rate)) for s, e in spans]


def recognise(visit_path: Path, lines: Path, replies_dir: Path, out: Path) -> None:
    """What the system hears from the real takes: each spoken line decoded with the job prompt, read-backs masked as
    in the synthetic runs, and the tech's replies to questions from the synthetic (clean) voice, as a simulation."""
    import json

    from fvr.asr import transcribe
    from live.render import heard_text, job_prompt, masked_readback, replies
    from live.scenario import REPLY

    visit = load(visit_path)
    prompt, heard = job_prompt(visit, with_fields=False), {}
    for t in visit.turns:
        if t.speaker == "device":
            if t.text.startswith("reading back"):
                heard[t.id] = {"text": t.text, "heard": masked_readback(t.text), "words": []}
            continue
        d = transcribe(str(lines / f"{visit.id}-{t.id}.wav"), prompt)
        heard[t.id] = {"text": d.text, "heard": heard_text(d.words), "words": d.words}
    for k, text in enumerate(replies(visit)):
        d = transcribe(str(replies_dir / f"{visit.id}-r{k}.wav"), prompt)
        heard[REPLY + text] = {"text": d.text, "heard": heard_text(d.words), "words": d.words}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(heard, indent=1))


def main() -> None:
    import sys

    if sys.argv[1:2] == ["--recognise"]:
        recognise(*map(Path, sys.argv[2:6]))
        return
    p = argparse.ArgumentParser()
    p.add_argument("take", type=Path)
    p.add_argument("visit", type=Path)
    p.add_argument("first")
    p.add_argument("last")
    p.add_argument("out", type=Path)
    p.add_argument("--align", action="store_true", help="line words up with the script instead of cutting at pauses")
    a = p.parse_args()
    visit = load(a.visit)
    ids = [t.id for t in visit.turns]
    lines = [t for t in visit.turns[ids.index(a.first) : ids.index(a.last) + 1] if t.speaker != "device"]
    audio, rate = sf.read(a.take, dtype="float32")
    texts = [t.text for t in lines]
    spans = align(texts, timed_words(a.take), rate) if a.align else cut(audio, rate, len(lines))
    if spans is None:
        raise SystemExit(f"could not cut {a.take.name} into {len(lines)} lines at the pauses")
    a.out.mkdir(parents=True, exist_ok=True)
    pad = int(0.15 * rate)
    for t, (start, end) in zip(lines, spans, strict=True):
        sf.write(a.out / f"{visit.id}-{t.id}.wav", audio[max(0, start - pad) : end + pad], rate, subtype="PCM_16")
        print(f"line {t.id}: {(end - start) / rate:.1f} s")


if __name__ == "__main__":
    main()
