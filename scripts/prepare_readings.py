"""Synthetic readings set (labelled synthetic) for developing and testing the reading verifier.

Sentence templates differ from the human recording script so the human recordings stay a fair held-out test. Every
reading carries its truth and whether a careful system should ask anyway (unit not said, self-correction,
approximate value). Dev voices tune; test voices only score.
Usage: python scripts/prepare_readings.py
"""

import json
import random
from pathlib import Path

from fvr.audio import mix, tts
from fvr.paths import portable
from fvr.synth import say_number

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/pilot.json").read_text())
WORK = Path(CONFIG["work_dir"]).expanduser() / "readings"
NOISE = Path(CONFIG["noise_dir"]).expanduser()
SEED = 20261119
NOISES = [("clean", None, None), ("ac_5", "AirConditioner", 5), ("babble_5", "Babble", 5)]

# (trade, label, unit key, spoken unit options, low, high, decimals)
QUANTITIES = [
    ("hvac", "suction pressure", "psi", ["P S I", "psi"], 105, 145, 0),
    ("hvac", "liquid line pressure", "psi", ["P S I"], 280, 410, 0),
    ("hvac", "superheat", "degrees", ["degrees"], 6, 18, 0),
    ("hvac", "subcooling", "degrees", ["degrees"], 6, 14, 0),
    ("hvac", "supply air", "degrees", ["degrees"], 52, 60, 0),
    ("hvac", "compressor current", "amps", ["amps"], 9, 22, 1),
    ("hvac", "blower current", "amps", ["amps"], 2, 7, 1),
    ("hvac", "line voltage", "volts", ["volts"], 228, 246, 0),
    ("hvac", "control voltage", "volts", ["volts"], 23, 28, 1),
    ("hvac", "gas manifold pressure", "inches_wc", ["inches of water column"], 3, 4, 1),
    ("hvac", "flame signal", "microamps", ["micro amps"], 1, 6, 1),
    ("plumbing", "outlet temperature", "degrees", ["degrees"], 118, 140, 0),
    ("plumbing", "static water pressure", "psi", ["P S I", "psi"], 45, 85, 0),
    ("plumbing", "thermocouple output", "millivolts", ["millivolts"], 18, 30, 0),
    ("electrical", "line to neutral", "volts", ["volts"], 116, 124, 0),
    ("electrical", "load current", "amps", ["amps"], 8, 40, 0),
    ("electrical", "ground resistance", "ohms", ["ohms"], 5, 40, 0),
]
CONTEXT = {
    "hvac": "HVAC service call, no cooling. Equipment on site: Carrier condenser, model 24ACC636A003; Goodman "
    "furnace, model GMVC960804CN. Parts and terms: contactor, dual run capacitor, TXV, superheat, subcooling.",
    "plumbing": "PLUMBING service call, no hot water. Equipment on site: Rheem water heater, model XG50T06EC36U1. "
    "Parts and terms: anode rod, thermocouple, T&P valve, expansion tank.",
    "electrical": "ELECTRICAL service call, breaker keeps tripping. Equipment on site: Square D panel, model "
    "QO130L200PG. Parts and terms: bus bar, neutral, GFCI, AFCI, main breaker.",
}
CONFUSABLE = [13, 14, 15, 16, 17, 18, 19, 30, 40, 50, 60, 70, 80, 90]  # teens and tens that sound alike
CONFUSABLE_LABELS = {"superheat", "subcooling", "compressor current", "load current", "ground resistance"}


def _value(q, rng, confusable=False):
    _, _, _, _, lo, hi, dec = q
    if confusable:
        v = rng.choice(CONFUSABLE)
        return v, str(v)
    v = round(rng.uniform(lo, hi), dec) if dec else rng.randint(int(lo), int(hi))
    return v, (f"{v:.{dec}f}" if dec else str(v))


def _truth(written, unit, spoken_unit, ask):
    return {"value": f"{float(written):g}", "unit": unit, "unit_spoken": spoken_unit, "ask": ask}


def make_utterance(kind: str, rng: random.Random) -> dict:
    trade = rng.choice(["hvac", "electrical"] if kind == "confusable" else ["hvac", "hvac", "plumbing", "electrical"])
    qs = [q for q in QUANTITIES if q[0] == trade]
    pool = [q for q in qs if q[1] in CONFUSABLE_LABELS] if kind == "confusable" else qs
    q = rng.choice(pool)
    _, label, unit, spoken_units, *_, dec = q
    su = rng.choice(spoken_units)
    v, w = _value(q, rng, confusable=(kind == "confusable"))
    dec = 0 if kind == "confusable" else dec
    s = say_number(v, dec, rng)
    if kind in ("plain", "confusable"):
        return {"trade": trade, "spoken": f"{label.capitalize()} is {s} {su}.", "truth": [_truth(w, unit, True, False)]}
    if kind == "nounit":
        return {"trade": trade, "spoken": f"{label.capitalize()} is {s}.", "truth": [_truth(w, unit, False, True)]}
    if kind == "approx":
        return {
            "trade": trade,
            "spoken": f"{label.capitalize()} is about {s} {su}.",
            "truth": [_truth(w, unit, True, True)],
        }
    if kind == "correction":
        v0, _ = _value(q, rng)
        s0 = say_number(v0, dec, rng)
        cue = rng.choice(["no wait", "I mean", "sorry"])
        return {
            "trade": trade,
            "spoken": f"{label.capitalize()} is {s0}... {cue}, {s} {su}.",
            "truth": [_truth(w, unit, True, True)],
        }
    if kind == "multi":
        q2 = rng.choice([x for x in qs if x != q])
        _, label2, unit2, spoken2, *_, dec2 = q2
        v2, w2 = _value(q2, rng)
        s2 = say_number(v2, dec2, rng)
        return {
            "trade": trade,
            "spoken": f"{label.capitalize()} is {s} {su}, and {label2} is {s2} {rng.choice(spoken2)}.",
            "truth": [_truth(w, unit, True, False), _truth(w2, unit2, True, False)],
        }
    raise ValueError(kind)


def noise_file(split: str, kind: str, seed: int) -> Path:
    folder = NOISE / ("noise_test" if split == "test" else "noise_train")
    return random.Random(seed).choice(sorted(folder.glob(f"{kind}_*.wav")))


def main() -> None:
    rng = random.Random(SEED)
    kinds = (
        ["plain"] * 30 + ["confusable"] * 20 + ["nounit"] * 20 + ["approx"] * 10 + ["correction"] * 20 + ["multi"] * 20
    )
    voices = CONFIG["synthetic"]["voices"]
    rows = []
    for n, kind in enumerate(kinds):
        u = make_utterance(kind, rng)
        split = "dev" if n % 3 == 0 else "test"
        voice = voices[split][n % len(voices[split])]
        uid = f"r{n:03d}"
        clean = WORK / "clean" / f"{uid}.wav"
        tts(u["spoken"], voice, clean)
        for k, (name, nkind, snr) in enumerate(NOISES):
            audio = clean
            seed = SEED + 10 * n + k
            if nkind:
                audio = WORK / name / f"{uid}.wav"
                mix(clean, noise_file(split, nkind, seed), snr, seed, audio)
            rows.append(
                {
                    "utt_id": uid,
                    "kind": kind,
                    "split": split,
                    "voice": voice,
                    "source": "synthetic-tts",
                    "noise": name,
                    "audio": portable(audio),
                    "spoken_text": u["spoken"],
                    "truth": u["truth"],
                    "prompts": {"none": None, "job": CONTEXT[u["trade"]]},
                }
            )
    out = ROOT / "results/readings/manifest.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"{len(kinds)} utterances, {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
