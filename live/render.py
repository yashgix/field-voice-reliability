"""The ASR condition: each spoken line voiced by macOS, mixed with noise and decoded by local Whisper.

Words Whisper is unsure of are marked with ~ so every arm sees the same confidence signal. The tech's possible replies
to questions go through the same pipeline. Headset prompts are kept as written. Scripted read-backs have their numbers
masked: the script writes them from the truth, and a real headset would read back what it heard, which this offline
replay cannot know.
"""

import argparse
import json
import random
import re
from pathlib import Path

from fvr.asr import transcribe
from fvr.audio import mix, tts
from fvr.synth import CATALOG
from live import tech
from live.scenario import REPLY, Visit, answer_text, load

VOICES = {"dev": {"tech": "Samantha", "customer": "Daniel"}, "test": {"tech": "Karen", "customer": "Rishi"}}
NOISE, SNR_DB = "Babble", 0.0
LOW_PROB = 0.5
NUMBER_WORDS = (
    "zero oh one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred point"
).split()
NUMBER = re.compile(r"\b(" + "|".join(NUMBER_WORDS) + r"|\d+(\.\d+)?)\b")


FIELD_TERMS = [
    "suction pressure",
    "head pressure",
    "superheat",
    "subcooling",
    "supply air",
    "return air",
    "delta T",
    "temperature rise",
    "compressor amps",
    "condenser fan",
    "blower amps",
    "capacitor",
    "microfarads",
    "line voltage",
    "static pressure",
    "gas pressure",
    "flame sensor",
    "microamps",
]  # fmt: skip  (the spec's reading fields, spoken)
TYPE_KEYS = {"condens": "condenser", "rooftop": "condenser", "split": "heat pump", "heat pump": "heat pump",
             "furnace": "furnace", "heater": "furnace"}  # fmt: skip


def job_prompt(visit: Visit, with_fields: bool) -> str:
    """The pilot's job-record prompt: equipment on site and part terms by equipment type, never readings. With
    `with_fields`, also the spec's measurement words."""
    gear = "; ".join(f"{e['make']} {e['type'].replace('_', ' ')}, model {e['model']}" for e in visit.equipment)
    terms: list[str] = []
    for e in visit.equipment:
        for key, kind in TYPE_KEYS.items():
            if key in e["type"].lower():
                terms += [t for t in CATALOG[kind][2] if t not in terms]
    if with_fields:
        terms += [t for t in FIELD_TERMS if t not in terms]
    return f"HVAC service call. Equipment on site: {gear}. Parts and terms: {', '.join(terms)}."


def redecode(visit: Visit, base: Path, work: Path, prompt: str) -> dict[str, dict]:
    """Decode the exact noisy audio of an earlier render again, this time with a context prompt. Cached in `work`."""
    out_file = work / f"{visit.id}.asr.json"
    out = json.loads(out_file.read_text()) if out_file.exists() else {}
    earlier = json.loads((base / f"{visit.id}.asr.json").read_text())
    texts = {text: k for k, text in enumerate(replies(visit))}
    if all(key in out for key in earlier):
        return out
    for key, row in earlier.items():
        if key in out:
            continue
        if not row["words"] and not key.startswith(REPLY):  # a masked read-back, not audio
            out[key] = row
            continue
        name = f"r{texts[key[len(REPLY) :]]}" if key.startswith(REPLY) else key
        decode = transcribe(str(base / "noisy" / f"{visit.id}-{name}.wav"), prompt)
        out[key] = {"text": decode.text, "heard": heard_text(decode.words), "words": decode.words, "prompt": prompt}
    work.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(out, indent=1))
    return out


def heard_text(words: list[tuple[str, float]]) -> str:
    return " ".join(("~" if p < LOW_PROB else "") + w.strip() for w, p in words if w.strip())


def masked_readback(text: str) -> str:
    return re.sub(r"(… ?)+", "… ", NUMBER.sub("…", text)).strip()


def _decode(text: str, voice: str, noise: Path, seed: int, clean: Path, noisy: Path) -> dict:
    tts(text, voice, clean)
    mix(clean, noise, SNR_DB, seed, noisy)
    decode = transcribe(str(noisy), None)
    return {"text": decode.text, "heard": heard_text(decode.words), "words": decode.words}


def replies(visit: Visit) -> list[str]:
    """Everything the tech may say when asked: scripted answers, repeats of reading lines, the neutral reply."""
    from live.arms import UNPLANNED_ANSWER

    answers = [answer_text(visit, e) for t in visit.turns for e in t.effects if e["op"] == "ambiguous"]
    repeats = [t.text for t in visit.turns if any(e["op"] in ("reading", "revise") for e in t.effects)]
    return [*dict.fromkeys([*answers, *repeats, UNPLANNED_ANSWER, *tech.possible(visit)])]


def _noises(noise_dir: Path, split: str) -> list[Path]:
    return sorted((noise_dir / ("noise_test" if split == "test" else "noise_train")).glob(f"{NOISE}_*.wav"))


def _add_replies(visit: Visit, split: str, noise_dir: Path, work: Path, seed: int, out: dict) -> bool:
    """Voice and recognise replies not rendered yet, each with its own seeded noise. Returns whether any were added."""
    added = False
    for k, text in enumerate(replies(visit)):
        if REPLY + text in out:
            continue
        rng = random.Random(f"{seed}-{visit.id}-{text}")
        clean, noisy = work / "clean" / f"{visit.id}-r{k}.wav", work / "noisy" / f"{visit.id}-r{k}.wav"
        noise = rng.choice(_noises(noise_dir, split))
        out[REPLY + text] = _decode(text, VOICES[split]["tech"], noise, rng.randrange(10**6), clean, noisy)
        added = True
    return added


def render(visit: Visit, split: str, noise_dir: Path, work: Path, seed: int) -> dict[str, dict]:
    """Recognised text and word probabilities per line and per possible reply, cached in `work`. Replies are voiced
    and mixed separately, so a repeat is a new utterance with its own noise, and every arm hears the same audio.
    Replies added to the policy later are rendered on top of an existing cache, which stays as it was."""
    out_file = work / f"{visit.id}.asr.json"
    if out_file.exists():
        out = json.loads(out_file.read_text())
        if _add_replies(visit, split, noise_dir, work, seed, out):
            out_file.write_text(json.dumps(out, indent=1))
        return out
    noises = _noises(noise_dir, split)
    rng, reply_rng, out = random.Random(f"{seed}-{visit.id}"), random.Random(f"{seed}-{visit.id}-replies"), {}
    for t in visit.turns:
        if t.speaker == "device":
            if t.text.startswith("reading back"):
                out[t.id] = {"text": t.text, "heard": masked_readback(t.text), "words": []}
            continue
        clean, noisy = work / "clean" / f"{visit.id}-{t.id}.wav", work / "noisy" / f"{visit.id}-{t.id}.wav"
        out[t.id] = _decode(t.text, VOICES[split][t.speaker], rng.choice(noises), rng.randrange(10**6), clean, noisy)
    for k, text in enumerate(replies(visit)):
        clean, noisy = work / "clean" / f"{visit.id}-r{k}.wav", work / "noisy" / f"{visit.id}-r{k}.wav"
        out[REPLY + text] = _decode(
            text, VOICES[split]["tech"], reply_rng.choice(noises), reply_rng.randrange(10**6), clean, noisy
        )
    out_file.write_text(json.dumps(out, indent=1))
    return out


def main() -> None:
    """Render visits once before running arms in parallel: python -m live.render VISIT.json... [--split dev|test]"""
    from live.run import heard_lines

    p = argparse.ArgumentParser()
    p.add_argument("visits", nargs="+", type=Path)
    p.add_argument("--split", default="dev", choices=["dev", "test"])
    a = p.parse_args()
    for path in a.visits:
        print(path.name, len(heard_lines(load(path), "asr", a.split)), "lines rendered")


if __name__ == "__main__":
    main()
