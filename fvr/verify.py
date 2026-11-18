"""Detect-and-recover retrieval, acoustic verification and the field safeguard.

The safeguard never writes a value the transcript did not contain: it only accepts a field or asks to confirm it.
"""

from dataclasses import dataclass

import jellyfish

from fvr.fields import extract_id_runs, extract_readings
from fvr.normalize import canonical_id, canonical_text, canonical_tokens, contains_id


@dataclass
class Record:
    ids: list[str]
    terms: list[str]


@dataclass
class Thresholds:
    id_ratio: float = 0.6  # edit similarity for an ID near-miss
    term_jw: float = 0.88  # Jaro-Winkler on phonetic keys for a term near-miss
    accept_margin: float = 6.0  # nats a context-shaped transcript may lose vs the unbiased one and still be accepted
    min_prob: float = 0.35  # word probability below which a critical field is confirmed


def _edit_ratio(a: str, b: str) -> float:
    return 1 - jellyfish.levenshtein_distance(a, b) / max(len(a), len(b), 1)


def _phonetic(text: str) -> str:
    return " ".join(jellyfish.metaphone(w) for w in text.split())


def _ngrams(tokens: list[str], n: int) -> list[str]:
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def _id_near_misses(tokens: list[str], record_ids: list[str], th: Thresholds) -> list[str]:
    spans = [g.replace(" ", "") for n in (1, 2, 3, 4) for g in _ngrams(tokens, n)]
    spans = [s for s in spans if any(c.isdigit() for c in s)]
    out = []
    for rid in record_ids:
        target = canonical_id(rid)
        if target in spans:
            continue
        if any(_edit_ratio(s, target) >= th.id_ratio for s in spans):
            out.append(rid)
    return out


def _term_near_misses(tokens: list[str], terms: list[str], th: Thresholds) -> list[str]:
    text = f" {' '.join(tokens)} "
    out = []
    for term in terms:
        t = canonical_text(term)
        if not t or f" {t} " in text:
            continue
        n = len(t.split())
        key = _phonetic(t)
        for g in _ngrams(tokens, n):
            if jellyfish.jaro_winkler_similarity(_phonetic(g), key) >= th.term_jw:
                out.append(term)
                break
    return out


def retrieve(hyp: str, record: Record, th: Thresholds) -> list[str]:
    """Error-aware selective retrieval: only record items with a near-miss in the unbiased transcript."""
    tokens = canonical_tokens(hyp)
    return _id_near_misses(tokens, record.ids, th) + _term_near_misses(tokens, record.terms, th)


def selective_prompt(items: list[str]) -> str:
    return "Terms: " + ", ".join(items) + "."


def accept_rewrite(lp_new: float, lp_old: float, th: Thresholds) -> bool:
    """Keep a context-shaped transcript only if the audio, scored without context, nearly as well supports it."""
    return lp_new >= lp_old - th.accept_margin


def _min_prob(words: list[tuple[str, float]], piece_ok) -> float:
    probs = [p for w, p in words if piece_ok(canonical_id(w))]
    return min(probs) if probs else 0.0


def field_decisions(
    text: str, words: list[tuple[str, float]], record: Record, th: Thresholds, unbiased: str | None = None
) -> list[tuple[tuple[str, str], str]]:
    """Accept or confirm each critical field in `text`. Never edits a value.

    An ID run that spells a record ID in whole tokens is reported as that ID; otherwise as the run itself.
    """
    out = []
    for run in extract_id_runs(text):
        on_record = next((canonical_id(r) for r in record.ids if contains_id(run, r)), None)
        value = on_record or run
        flat = value.replace(" ", "")
        p = _min_prob(words, lambda w, flat=flat: len(w) > 1 and w in flat)
        disputed = unbiased is not None and not contains_id(unbiased, flat)
        ok = on_record is not None and p >= th.min_prob and not disputed
        out.append((("id", value), "accept" if ok else "confirm"))
    unbiased_readings = set(extract_readings(unbiased)) if unbiased is not None else None
    for r in extract_readings(text):
        parts = {canonical_id(v) for v in r.value.split("/")}
        p = _min_prob(words, lambda w, parts=parts: w in parts)
        disputed = unbiased_readings is not None and r not in unbiased_readings
        out.append((("reading", f"{r.value}|{r.unit}"), "accept" if p >= th.min_prob and not disputed else "confirm"))
    return out
