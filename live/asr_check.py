"""Compare recognition of the same noisy audio decoded with and without a job-record prompt. No model calls.

Usage: python -m live.asr_check VISIT.json... [--split test] [--contexts none,job,job+fields]
Counts, over every scripted line, what reached the text: reading values, measurement words, both together, equipment
identifiers, and what the prompt may have added: numbers and identifiers never said, measurement words never said,
runaway output.
"""

import argparse
import re
from collections import Counter
from pathlib import Path

from fvr.normalize import contains_id
from live.entries import numbers, said, same
from live.run import heard_lines
from live.scenario import load
from live.tech import PATTERNS

ANY_TERM = re.compile("|".join(PATTERNS.values()), re.I)


def _term(field: str) -> re.Pattern:
    return re.compile(PATTERNS[field.removesuffix("_after")], re.I)


def check_line(gold: str, heard: str, effects: list[dict], ids: list[str]) -> Counter:
    c, heard = Counter(), heard.replace("~", "")
    for e in effects:
        if e["op"] in ("reading", "revise") and said(str(e["value"]), gold):
            got_value = said(str(e["value"]), heard)
            c["values"] += 1
            c["value heard"] += got_value
            if _term(e["field"]).search(gold):
                c["terms"] += 1
                got_term = bool(_term(e["field"]).search(heard))
                c["term heard"] += got_term
                c["pair heard"] += got_value and got_term
        if e["op"] == "equipment":
            c["identifiers"] += 1
            c["identifier heard"] += contains_id(heard, str(e["value"]))
    gold_numbers = numbers(gold)
    c["numbers never said"] += sum(
        not any(same(n, g) for g in gold_numbers) for n in numbers(heard) if "." in n or len(n) > 1
    )
    c["identifiers never said"] += sum(contains_id(heard, i) and not contains_id(gold, i) for i in ids)
    c["terms never said"] += len(
        set(m.lower() for m in ANY_TERM.findall(heard)) - set(m.lower() for m in ANY_TERM.findall(gold))
    )
    c["runaway lines"] += len(heard.split()) > 3 * len(gold.split()) + 5
    return c


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("visits", nargs="+", type=Path)
    p.add_argument("--split", default="test")
    p.add_argument("--contexts", default="none,job,job+fields")
    a = p.parse_args()
    rows = {}
    for context in a.contexts.split(","):
        total = Counter()
        for path in a.visits:
            visit = load(path)
            heard = heard_lines(visit, "asr", a.split, context)
            ids = [str(e[f]) for e in visit.equipment for f in ("model", "serial")]
            for t in visit.turns:
                if t.speaker != "device":
                    total += check_line(t.text, heard.get(t.id, ""), t.effects, ids)
        rows[context] = total
    keys = ["value heard", "term heard", "pair heard", "identifier heard", "numbers never said",
            "identifiers never said", "terms never said", "runaway lines"]  # fmt: skip
    base = {"value heard": "values", "term heard": "terms", "pair heard": "terms", "identifier heard": "identifiers"}
    print("| measure | " + " | ".join(rows) + " |\n|---" * 1 + "|---" * len(rows) + "|")
    for k in keys:
        cells = [f"{r[k]}/{r[base[k]]}" if k in base else str(r[k]) for r in rows.values()]
        print(f"| {k} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
