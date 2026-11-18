"""Collect the evidence the detect-and-recover and hybrid arms need: selective re-decodes and acoustic scores.

Retrieval thresholds are fixed in advance (fvr.verify.Thresholds defaults); the accept margin and minimum word
probability are swept later on the dev split only. Resumable.
Usage: python scripts/run_arms.py results/synthetic
"""

import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

from fvr.asr import transcribe
from fvr.normalize import canonical_text
from fvr.paths import resolve
from fvr.scorer import Scorer
from fvr.synth import job_record_terms
from fvr.verify import Record, Thresholds, retrieve, selective_prompt

RECORD_CONDITIONS = ["job", "stale", "wrong"]


def records_for(jobs: dict, job_id: str) -> dict[str, Record]:
    from fvr.context import wrong_job
    from fvr.synth import Equipment, Job

    def to_job(d):
        return Job(
            d["job_id"],
            d["trade"],
            d["complaint"],
            [Equipment(**e) for e in d["equipment"]],
            [Equipment(**e) for e in d["stale_equipment"]],
        )

    all_jobs = [to_job(d) for d in jobs.values()]
    job = next(j for j in all_jobs if j.job_id == job_id)
    other = wrong_job(job, all_jobs)

    def rec(j, equipment):
        return Record([e.model for e in equipment], [e.brand for e in equipment] + job_record_terms(j))

    return {
        "job": rec(job, job.equipment),
        "stale": rec(job, job.stale_equipment),
        "wrong": rec(other, other.equipment),
    }


def main(folder: Path) -> None:
    rows = [json.loads(line) for line in (folder / "manifest.jsonl").open()]
    jobs = {j["job_id"]: j for j in json.loads((folder / "jobs.json").read_text())}
    decodes = {}
    for line in (folder / "decodes.jsonl").open():
        d = json.loads(line)
        decodes[(d["utt_id"], d["noise"], d["condition"])] = d
    out_path = folder / "arms.jsonl"
    done = {json.loads(line)["key"] for line in out_path.open()} if out_path.exists() else set()
    th = Thresholds()
    with out_path.open("a") as out:
        for n, row in enumerate(rows):
            key = f"{row['utt_id']}|{row['noise']}"
            if key in done or (row["utt_id"], row["noise"], "none") not in decodes:
                continue
            h0 = decodes[(row["utt_id"], row["noise"], "none")]
            start = time.perf_counter()
            scorer = Scorer(resolve(row["audio"]))
            cache = {}

            def score(text, scorer=scorer, cache=cache):
                if text not in cache:
                    cache[text] = scorer.logprob(text)[0]
                return cache[text]

            evidence = {"lp_none": score(h0["text"]), "encode_seconds": time.perf_counter() - start}
            for cond, record in records_for(jobs, row["job_id"]).items():
                hc = decodes[(row["utt_id"], row["noise"], cond)]
                t = time.perf_counter()
                same = canonical_text(hc["text"]) == canonical_text(h0["text"])
                hybrid = {
                    "lp_context": evidence["lp_none"] if same else score(hc["text"]),
                    "score_seconds": time.perf_counter() - t,
                }
                items = retrieve(h0["text"], record, th)
                detect = {"items": items}
                if items:
                    t = time.perf_counter()
                    h1 = transcribe(resolve(row["audio"]), selective_prompt(items))
                    detect.update(
                        {"redecode": asdict(h1), "lp_redecode": score(h1.text), "seconds": time.perf_counter() - t}
                    )
                evidence[cond] = {"record": asdict(record), "hybrid": hybrid, "detect": detect}
            out.write(json.dumps({"key": key, **evidence}) + "\n")
            out.flush()
            if n % 50 == 0:
                print(f"{n}/{len(rows)}", flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
