"""Scoring: WER, jargon-term misses, critical-field correctness, safeguard outcomes, cluster bootstrap."""

import random
from collections import Counter

import jiwer

from fvr.fields import extract_readings
from fvr.normalize import canonical_id, canonical_text, contains_id, is_refrigerant


def wer(ref: str, hyp: str) -> tuple[int, int]:
    """(errors, reference words) on canonical text, so totals can be pooled."""
    r, h = canonical_text(ref), canonical_text(hyp)
    out = jiwer.process_words(r, h or "<empty>")
    return out.substitutions + out.deletions + out.insertions, len(r.split())


def term_hits(terms: list[str], hyp: str) -> list[bool]:
    padded = f" {canonical_text(hyp)} "
    return [f" {canonical_text(t)} " in padded for t in terms]


def ref_fields(row: dict) -> list[tuple[str, str]]:
    ids = [("id", canonical_id(i)) for i in row["ids"]]
    readings = [("reading", f"{v}|{u}") for v, u in row["readings"]]
    return ids + readings


def _matches(ref: tuple[str, str], got: tuple[str, str]) -> bool:
    """An ID matches if the output run spells it in whole tokens; a reading must be identical."""
    if ref[0] != got[0]:
        return False
    return contains_id(got[1], ref[1]) if ref[0] == "id" else ref[1] == got[1]


def fields_correct(row: dict, text: str) -> list[bool]:
    """Per reference field: is it present exactly in the hypothesis?"""
    found = Counter(f"{r.value}|{r.unit}" for r in extract_readings(text))
    out = [contains_id(text, i) for i in row["ids"]]
    for v, u in row["readings"]:
        key = f"{v}|{u}"
        out.append(found[key] > 0)
        found[key] -= 1
    return out


def context_insertions(row: dict, text: str, record_ids: list[str]) -> int:
    """Record IDs written in the output that the speaker did not say: context pushed into the transcript."""
    said = {canonical_id(i) for i in row["ids"]}
    ids = [r for r in record_ids if not is_refrigerant(canonical_id(r))]  # "R-410A" is a term, not equipment
    return sum(1 for r in ids if canonical_id(r) not in said and contains_id(text, r))


def safeguard_outcomes(row: dict, decisions: list[tuple[tuple[str, str], str]]) -> Counter:
    """Classify each reference field given (field, "accept"|"confirm") decisions for the extracted fields.

    A reference field the output never produced is a silent miss: nothing in the output points the technician at it.
    """
    pending = list(decisions)
    out = Counter()
    unmatched = []
    for f in ref_fields(row):
        hit = next((p for p in pending if _matches(f, p[0])), None)
        if hit:
            pending.remove(hit)
            out[f"correct_{hit[1]}"] += 1
        else:
            unmatched.append(f)
    for f in unmatched:
        same_type = next((p for p in pending if p[0][0] == f[0]), None)
        if same_type:
            pending.remove(same_type)
            out[f"wrong_{same_type[1]}"] += 1
        else:
            out["missed_silent"] += 1
    for p in pending:
        out[f"spurious_{p[1]}"] += 1
    return out


def silent_errors(c: Counter) -> int:
    return c["wrong_accept"] + c["missed_silent"] + c["spurious_accept"]


def bootstrap_diff(pairs: dict[str, tuple[float, float]], n: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    """Pooled mean difference and a 95% interval, resampling utterances. pairs: utt -> (sum of diffs, count)."""
    keys = sorted(pairs)
    total = sum(v[0] for v in pairs.values()) / max(1, sum(v[1] for v in pairs.values()))
    rng = random.Random(seed)
    stats = []
    for _ in range(n):
        sample = [pairs[rng.choice(keys)] for _ in keys]
        stats.append(sum(s[0] for s in sample) / max(1, sum(s[1] for s in sample)))
    stats.sort()
    return total, stats[int(0.025 * n)], stats[int(0.975 * n)]
