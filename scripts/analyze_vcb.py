"""Tables for the VoiceCodeBench real-speech check.

Safeguard here is the two-decode version only (no acoustic scoring): segments run past Whisper's 30 s window,
which the teacher-forced scorer does not handle yet. A code is accepted only when it is on the record and both the
plain and the record-prompted decodes contain it.
Usage: python scripts/analyze_vcb.py results/vcb
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from fvr.metrics import wer
from fvr.normalize import canonical_id, canonical_tokens, contains_id

UNITS = {
    "lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb", "kg": "kg", "kilogram": "kg", "kilograms": "kg",
    "in": "in", "inch": "in", "inches": "in", "ft": "ft", "foot": "ft", "feet": "ft", "mm": "mm",
    "millimeters": "mm", "cm": "cm", "centimeters": "cm", "g": "g", "grams": "g", "mg": "mg", "milligrams": "mg",
    "ml": "ml", "milliliters": "ml", "l": "l", "liters": "l", "oz": "oz", "ounces": "oz", "m": "m", "meters": "m",
    "gb": "gb", "tb": "tb", "mb": "mb", "w": "w", "watts": "w", "v": "v", "volts": "v",
}  # fmt: skip


def measurements(text: str) -> Counter:
    tokens = canonical_tokens(text)
    out = Counter()
    for a, b in zip(tokens, tokens[1:], strict=False):
        if re.fullmatch(r"\d+(\.\d+)?", a) and b in UNITS:
            out[(f"{float(a):g}", UNITS[b])] += 1
    return out


def main(folder: Path) -> None:
    rows = [json.loads(line) for line in (folder / "manifest.jsonl").open()]
    rows = [r for r in rows if r["noise"] == "clean"]  # the noisy copies were dropped mid-run to save time
    dec = defaultdict(dict)
    for line in (folder / "decodes.jsonl").open():
        d = json.loads(line)
        dec[(d["utt_id"], d["noise"])][d["condition"]] = d
    stats = defaultdict(Counter)
    for r in rows:
        ds = dec.get((r["utt_id"], r["noise"]))
        if not ds or len(ds) < 3:
            continue
        codes = r["codes"]
        ref_meas = measurements(r["ref_text"])
        none_text = ds["none"]["text"]
        for cond in ("none", "record", "wrong"):
            s = stats[(cond, r["noise"])]
            text = ds[cond]["text"]
            e, n = wer(r["ref_text"], text)
            s["wer_e"] += e
            s["wer_n"] += n
            s["codes"] += len(codes)
            ok = [contains_id(text, c) for c in codes]
            was = [contains_id(none_text, c) for c in codes]
            s["codes_ok"] += sum(ok)
            s["codes_broke"] += sum(w and not o for o, w in zip(ok, was, strict=True))
            s["codes_fixed"] += sum(o and not w for o, w in zip(ok, was, strict=True))
            hyp_meas = measurements(text)
            s["meas"] += sum(ref_meas.values())
            s["meas_ok"] += sum((ref_meas & hyp_meas).values())
            context = r["record_codes"] if cond == "record" else r["wrong_codes"] if cond == "wrong" else []
            said = {canonical_id(c) for c in codes}
            unsaid = [c for c in context if canonical_id(c) not in said]
            inserted = [c for c in unsaid if contains_id(text, c)]
            s["inserted"] += len(inserted)
            s["sec"] += ds[cond]["seconds"]
            s["rows"] += 1
            if cond == "record":
                for o, w in zip(ok, was, strict=True):
                    s["sg_correct_accept"] += o and w
                    s["sg_flagged"] += not (o and w)
                s["sg_inserted_accepted"] += sum(contains_id(none_text, c) for c in inserted)
    lines = [
        "# VoiceCodeBench real-speech check (human recordings, codes and measurements)\n",
        "| Condition | Noise | WER | Product codes exact | Broke vs none | Fixed vs none | Measurements exact | "
        "Unsaid record codes inserted | s/segment |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for (cond, noise), s in sorted(stats.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        lines.append(
            f"| {cond} | {noise} | {100 * s['wer_e'] / s['wer_n']:.1f}% | {s['codes_ok']}/{s['codes']} | "
            f"{s['codes_broke']} | {s['codes_fixed']} | {s['meas_ok']}/{s['meas']} | {s['inserted']} | "
            f"{s['sec'] / s['rows']:.1f} |"
        )
    lines.append("\nTwo-decode safeguard, record condition (accept a code only if both decodes agree):\n")
    for (cond, noise), s in sorted(stats.items()):
        if cond == "record":
            lines.append(
                f"- {noise}: {s['sg_correct_accept']} codes accepted correctly, {s['sg_flagged']} sent for "
                f"confirmation (correct or not), {s['sg_inserted_accepted']} unsaid record codes accepted"
            )
    (folder / "tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
