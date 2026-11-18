"""Format-priming comparison on utterances that say a model number (synthetic, labelled synthetic).

none / brand only / pattern (right format, every digit wrong) / stale record / correct record.
Usage: python scripts/analyze_format.py
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from fvr.metrics import bootstrap_diff
from fvr.normalize import contains_id

ROOT = Path(__file__).resolve().parents[1]
ORDER = ["none", "brand", "pattern", "stale", "job"]
NOISES = ["clean", "ac_5", "ac_0", "babble_5"]


def prompt_ids(prompt: str | None) -> list[str]:
    return re.findall(r"model ([A-Za-z0-9-]+)", prompt or "")


def main() -> None:
    rows = [json.loads(line) for line in (ROOT / "results/format/manifest.jsonl").open()]
    dec = defaultdict(dict)
    for f in ("results/synthetic/decodes.jsonl", "results/format/decodes.jsonl"):
        for line in (ROOT / f).open():
            d = json.loads(line)
            if d["condition"] in ORDER:
                dec[(d["utt_id"], d["noise"])][d["condition"]] = d
    lines = ["# Format-priming comparison (synthetic, utterances with a spoken model number)", ""]
    for split in ("test", "dev"):
        sub = [r for r in rows if r["split"] == split and len(dec[(r["utt_id"], r["noise"])]) == len(ORDER)]
        ok = defaultdict(Counter)
        paired = defaultdict(dict)
        inserted = Counter()
        for r in sub:
            ds = dec[(r["utt_id"], r["noise"])]
            base = [contains_id(ds["none"]["text"], i) for i in r["ids"]]
            for c in ORDER:
                hits = [contains_id(ds[c]["text"], i) for i in r["ids"]]
                for key in (c, f"{c}|{r['noise']}"):
                    ok[key]["n"] += len(hits)
                    ok[key]["ok"] += sum(hits)
                prev = paired[c].get(r["utt_id"], (0, 0))
                paired[c][r["utt_id"]] = (prev[0] + sum(hits) - sum(base), prev[1] + len(hits))
                said = {i.upper() for i in r["ids"]}
                prompt = r["prompts"].get(c) if c in ("brand", "pattern") else ds[c]["prompt"]
                inserted[c] += sum(contains_id(ds[c]["text"], p) for p in prompt_ids(prompt) if p.upper() not in said)
        lines += [
            f"## {split}: {len({r['utt_id'] for r in sub})} utterances x {len(NOISES)} noise conditions, "
            f"{ok['none']['n']} model numbers\n",
            "| Context | " + " | ".join(NOISES) + " | All | vs none (95% CI) | Unsaid prompt model numbers written |",
            "|---|" + "---|" * (len(NOISES) + 3),
        ]
        for c in ORDER:
            cells = [f"{100 * ok[f'{c}|{n}']['ok'] / max(1, ok[f'{c}|{n}']['n']):.0f}%" for n in NOISES]
            d = bootstrap_diff(paired[c]) if c != "none" else None
            ci = f"{100 * d[0]:+.1f} [{100 * d[1]:+.1f}, {100 * d[2]:+.1f}]" if d else "-"
            ins = inserted[c] if c not in ("none", "brand") else "-"
            all_ = f"{100 * ok[c]['ok'] / max(1, ok[c]['n']):.1f}% ({ok[c]['ok']}/{ok[c]['n']})"
            lines.append(f"| {c} | " + " | ".join(cells) + f" | {all_} | {ci} | {ins} |")
        lines.append("")
    (ROOT / "results/format/tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
