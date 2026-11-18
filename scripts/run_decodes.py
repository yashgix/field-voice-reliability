"""Decode every manifest row under every context condition. Resumable: finished keys are skipped.

Usage: python scripts/run_decodes.py results/synthetic [noise,noise,...]
Conditions with an identical prompt for the same audio share one decode (recorded as `shared_with`).
"""

import json
import sys
from dataclasses import asdict
from pathlib import Path

from fvr.asr import DECODE, MODEL, transcribe
from fvr.paths import resolve


def key(row: dict, condition: str) -> str:
    return f"{row['utt_id']}|{row['noise']}|{condition}"


def main(folder: Path, noises: set[str] | None) -> None:
    rows = [json.loads(line) for line in (folder / "manifest.jsonl").open()]
    rows = [r for r in rows if noises is None or r["noise"] in noises]
    out_path = folder / "decodes.jsonl"
    done = {json.loads(line)["key"] for line in out_path.open()} if out_path.exists() else set()
    with out_path.open("a") as out:
        for n, row in enumerate(rows):
            by_prompt = {}
            for condition, prompt in row["prompts"].items():
                k = key(row, condition)
                if k in done:
                    continue
                shared = by_prompt.get(prompt)
                d = shared[1] if shared else transcribe(resolve(row["audio"]), prompt)
                by_prompt.setdefault(prompt, (condition, d))
                rec = {
                    "key": k,
                    "utt_id": row["utt_id"],
                    "noise": row["noise"],
                    "condition": condition,
                    "prompt": prompt,
                    "model": MODEL,
                    "decode": {**DECODE, "temperature": list(DECODE["temperature"])},
                    **asdict(d),
                    "shared_with": shared[0] if shared else None,
                }
                out.write(json.dumps(rec) + "\n")
                out.flush()
            if n % 50 == 0:
                print(f"{n}/{len(rows)} rows", flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]), set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None)
