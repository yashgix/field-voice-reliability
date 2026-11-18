"""Compare an author's labels with a blind reviewer's, line by line and in the final record.

Usage: python -m live.agree AUTHOR.json REVIEWER.json
"""

import json
import sys

from live.scenario import load, truth


def _canon(effects: list[dict]) -> set[str]:
    return {json.dumps({k: v for k, v in e.items() if k not in ("answer", "uom")}, sort_keys=True) for e in effects}


def main() -> None:
    a, b = load(sys.argv[1]), load(sys.argv[2])
    differ = [(x, y) for x, y in zip(a.turns, b.turns, strict=True) if _canon(x.effects) != _canon(y.effects)]
    for x, y in differ:
        print(
            f"line {x.id}: {x.text}\n  author:   {sorted(_canon(x.effects))}\n  reviewer: {sorted(_canon(y.effects))}"
        )
    ta, tb = truth(a.turns), truth(b.turns)
    same_final = (ta.readings, ta.work, ta.equipment, set(ta.unresolved)) == (
        tb.readings, tb.work, tb.equipment, set(tb.unresolved))  # fmt: skip
    print(f"{a.id}: {len(differ)} of {len(a.turns)} lines differ, final record {'same' if same_final else 'differs'}")


if __name__ == "__main__":
    main()
