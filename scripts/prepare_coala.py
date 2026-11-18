"""Real human speech check on COALA (CC0): rare plant terms with the right, no, or another script's term list.

Rare term = alphabetic word of 4+ letters that Whisper's tokenizer splits into 2+ pieces (not a common word to it).
Sample: 150 recordings by seed, half with real humming or technical background noise, half without, from scripts
with at least one rare term.
Usage: python scripts/prepare_coala.py
"""

import csv
import json
import random
import re
import subprocess
from pathlib import Path

from mlx_whisper.tokenizer import get_tokenizer

from fvr.paths import portable

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/pilot.json").read_text())
COALA = Path(CONFIG["coala_dir"]).expanduser()
SEED = 20261117
PER_GROUP = 75


def words(script: str) -> list[str]:
    return re.findall(r"[a-z]+", script.lower())


def main() -> None:
    meta = list(csv.DictReader((COALA / "metadata_ENG.csv").open(encoding="utf-8-sig")))
    scripts = {m["scriptId"]: m["script"] for m in meta}
    tok = get_tokenizer(True, num_languages=100)
    rare = {
        sid: sorted({w for w in words(s) if len(w) >= 4 and len(tok.encode(" " + w)) >= 2})
        for sid, s in scripts.items()
    }
    rng = random.Random(SEED)
    picked = []
    for noise in ("humming_or_technical_noise", "no_background_noise"):
        pool = [m for m in meta if m["background_noise_type"] == noise and rare[m["scriptId"]]]
        picked += rng.sample(pool, PER_GROUP)
    members = [f"audio/{m['file_name']}" for m in picked]
    subprocess.run(["bsdtar", "-xf", str(COALA.parent / "coala.rar"), "-C", str(COALA), *members], check=True)
    sids = sorted(scripts)
    rows = []
    for m in picked:
        other = rng.choice([s for s in sids if s != m["scriptId"] and rare[s]])
        terms, wrong = rare[m["scriptId"]], rare[other]
        rows.append(
            {
                "utt_id": m["file_name"].removesuffix(".wav"),
                "noise": "real_noise" if m["background_noise_type"] != "no_background_noise" else "quiet",
                "audio": portable(COALA / "audio" / m["file_name"]),
                "source": "coala-human",
                "speaker": m["participantId"],
                "ref_text": m["script"],
                "terms": terms,
                "wrong_terms": wrong,
                "prompts": {
                    "none": None,
                    "oracle": "Plant terms: " + ", ".join(terms) + ".",
                    "wrong": "Plant terms: " + ", ".join(wrong) + ".",
                },
            }
        )
    out = ROOT / "results/coala/manifest.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"{len(rows)} rows, {len({r['speaker'] for r in rows})} speakers -> {out}")


if __name__ == "__main__":
    main()
