"""Controlled format-priming test: which part of the job record helps model numbers?

Reuses the synthetic audio. New prompts, otherwise identical to the job record:
- brand: equipment brand and type, no model numbers;
- pattern: every model number with each digit replaced by a different random digit (letters, dashes and length
  kept), so the format is right and no digit value is.
none, stale and job decodes are reused from results/synthetic. Only utterances that say a model number are used.
Usage: python scripts/prepare_format.py
"""

import json
import random
import re
from pathlib import Path

from fvr.context import _record_prompt
from fvr.synth import Equipment, job_record_terms

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261118


def scramble_digits(model: str, rng: random.Random) -> str:
    return re.sub(r"\d", lambda m: rng.choice([d for d in "0123456789" if d != m.group()]), model)


def brand_prompt(trade: str, complaint: str, equipment: list[Equipment], terms: list[str]) -> str:
    gear = "; ".join(f"{e.brand} {e.type}" for e in equipment)
    return f"{trade.upper()} service call, {complaint}. Equipment on site: {gear}. Parts and terms: {', '.join(terms)}."


def main() -> None:
    from fvr.synth import Job

    jobs = {}
    for d in json.loads((ROOT / "results/synthetic/jobs.json").read_text()):
        eq = [Equipment(**e) for e in d["equipment"]]
        stale = [Equipment(**e) for e in d["stale_equipment"]]
        jobs[d["job_id"]] = Job(d["job_id"], d["trade"], d["complaint"], eq, stale)
    rng = random.Random(SEED)
    patterns = {
        j: [Equipment(e.type, e.brand, scramble_digits(e.model, rng)) for e in job.equipment] for j, job in jobs.items()
    }
    rows = []
    for line in (ROOT / "results/synthetic/manifest.jsonl").open():
        r = json.loads(line)
        if not r["ids"] or r["noise"] not in {"clean", "ac_5", "ac_0", "babble_5"}:
            continue
        job = jobs[r["job_id"]]
        terms = job_record_terms(job)
        r["prompts"] = {
            "brand": brand_prompt(job.trade, job.complaint, job.equipment, terms),
            "pattern": _record_prompt(job.trade, job.complaint, patterns[r["job_id"]], terms),
        }
        rows.append(r)
    out = ROOT / "results/format/manifest.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"{len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
