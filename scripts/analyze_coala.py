"""Tables for the COALA real-speech check: rare-term misses and unsaid-term insertions per context.

Usage: python scripts/analyze_coala.py results/coala
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from fvr.metrics import bootstrap_diff, term_hits, wer
from fvr.normalize import canonical_tokens

CONDITIONS = ["none", "oracle", "wrong"]


def main(folder: Path) -> None:
    rows = [json.loads(line) for line in (folder / "manifest.jsonl").open()]
    dec = defaultdict(dict)
    for line in (folder / "decodes.jsonl").open():
        d = json.loads(line)
        dec[(d["utt_id"], d["noise"])][d["condition"]] = d
    stats = defaultdict(Counter)
    paired = defaultdict(dict)
    examples = []
    for r in rows:
        ds = dec[(r["utt_id"], r["noise"])]
        base = term_hits(r["terms"], ds["none"]["text"])
        ref_words = set(canonical_tokens(r["ref_text"]))
        for cond in CONDITIONS:
            text = ds[cond]["text"]
            hits = term_hits(r["terms"], text)
            unsaid = [w for w in r["wrong_terms"] if w not in ref_words]
            inserted = [w for w, h in zip(unsaid, term_hits(unsaid, text), strict=True) if h]
            for key in (cond, f"{cond}|{r['noise']}"):
                s = stats[key]
                e, n = wer(r["ref_text"], text)
                s["wer_e"] += e
                s["wer_n"] += n
                s["terms"] += len(hits)
                s["missed"] += hits.count(False)
                s["fixed"] += sum(h and not b for h, b in zip(hits, base, strict=True))
                s["broke"] += sum(b and not h for h, b in zip(hits, base, strict=True))
                s["unsaid_offered"] += len(unsaid)
                s["inserted"] += len(inserted)
                s["rows"] += 1
            paired[cond][r["utt_id"]] = (sum(hits) - sum(base), len(hits))
            if inserted:
                examples.append(f'- {cond}: inserted {inserted}. Ref: "{r["ref_text"]}" Hyp: "{text}"')
    lines = [
        "# COALA real-speech check (human read speech, manufacturing requests)\n",
        "| Condition | Subset | WER | Rare-term misses | Fixed vs none | Broke vs none | Unsaid listed terms written | "
        "Term recall vs none (95% CI) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for key in sorted(stats, key=lambda k: (k.split("|")[1:] or [""], CONDITIONS.index(k.split("|")[0]))):
        s = stats[key]
        cond, *sub = key.split("|")
        diff = bootstrap_diff(paired[cond]) if cond != "none" and not sub else None
        ci = f"{100 * diff[0]:+.1f} pts [{100 * diff[1]:+.1f}, {100 * diff[2]:+.1f}]" if diff else "-"
        lines.append(
            f"| {cond} | {sub[0] if sub else 'all'} | {100 * s['wer_e'] / s['wer_n']:.1f}% | "
            f"{s['missed']}/{s['terms']} | {s['fixed']} | {s['broke']} | {s['inserted']}/{s['unsaid_offered']} | {ci} |"
        )
    lines += ["\nEvery insertion of an unsaid listed term:\n", *(examples or ["- none"])]
    (folder / "tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
