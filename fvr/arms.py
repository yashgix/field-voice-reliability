"""The four arms as pure functions of cached evidence, so thresholds can be swept without re-decoding.

B  baseline: no context.
P  prevent: job-record prompt before ASR.
D  detect and recover: no-context decode, error-aware selective retrieval from the record, re-decode with only the
   retrieved items, keep the re-decode only if the audio (scored without context) supports it.
H  hybrid: no-context and record-prompted decodes, keep the prompted one only if the audio supports it.
Every arm's fields then pass the safeguard, which accepts or asks to confirm and never edits.
"""

from dataclasses import dataclass

from fvr.normalize import canonical_text
from fvr.verify import Record, Thresholds, accept_rewrite, field_decisions

ARMS = ["B", "P", "D", "H"]


@dataclass
class ArmResult:
    text: str
    decisions: list
    seconds: float
    rewrote: bool


def _choose(
    base: dict, alt_text: str, alt_words: list, lp_alt: float, lp_base: float, record: Record, th: Thresholds
) -> tuple[str, list, bool]:
    if canonical_text(alt_text) == canonical_text(base["text"]):
        return base["text"], field_decisions(base["text"], base["words"], record, th), False
    if accept_rewrite(lp_alt, lp_base, th):
        return alt_text, field_decisions(alt_text, alt_words, record, th), True
    return base["text"], field_decisions(base["text"], base["words"], record, th, unbiased=alt_text), False


def run_arm(arm: str, decodes: dict, evidence: dict, cond: str, th: Thresholds) -> ArmResult:
    """decodes: condition -> decode dict; evidence: one row of arms.jsonl; cond: which record (job/stale/wrong)."""
    base = decodes["none"]
    ev = evidence[cond]
    record = Record(**ev["record"])
    if arm == "B":
        return ArmResult(base["text"], field_decisions(base["text"], base["words"], record, th), base["seconds"], False)
    if arm == "P":
        hc = decodes[cond]
        return ArmResult(hc["text"], field_decisions(hc["text"], hc["words"], record, th), hc["seconds"], False)
    if arm == "D":
        det = ev["detect"]
        if not det["items"]:
            return ArmResult(
                base["text"], field_decisions(base["text"], base["words"], record, th), base["seconds"], False
            )
        h1 = det["redecode"]
        text, decisions, rewrote = _choose(
            base, h1["text"], h1["words"], det["lp_redecode"], evidence["lp_none"], record, th
        )
        seconds = base["seconds"] + det["seconds"] + evidence["encode_seconds"]
        return ArmResult(text, decisions, seconds, rewrote)
    if arm == "H":
        hc = decodes[cond]
        seconds = base["seconds"] + hc["seconds"] + evidence["encode_seconds"] + ev["hybrid"]["score_seconds"]
        text, decisions, rewrote = _choose(
            base, hc["text"], hc["words"], ev["hybrid"]["lp_context"], evidence["lp_none"], record, th
        )
        return ArmResult(text, decisions, seconds, rewrote)
    raise ValueError(arm)
