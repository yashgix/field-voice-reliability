"""Reading verifier: accept a spoken measurement, or ask one focused question. Never edits or invents a value.

Rules, all on the transcript and Whisper's own word probabilities (prompt-free alignment pass):
- unclear_unit: a number after a measurement word, or before a word that sounds like a unit, but no valid unit;
  an integer glued to "A" ("60A": amps, a code part or a refrigerant) is confirmed, never accepted;
- no_value: a measurement word with no number after it in the same clause;
- low_confidence: a reading whose number word is below a probability floor (tuned on dev);
- correction: a self-correction cue ("no wait", "I mean") near the reading;
- approximate: "about", "maybe", "around" next to the reading;
- disagreement: optional second transcript (e.g. without job context) has a different reading set.
"""

import re
from dataclasses import dataclass

import jellyfish

from fvr.fields import Reading, extract_readings, reading_spans
from fvr.normalize import UNITS, canonical_tokens, is_refrigerant, token_groups

LABELS = {
    "pressure", "suction", "head", "discharge", "superheat", "subcooling", "temperature", "temp", "rise", "supply",
    "return", "outdoor", "voltage", "neutral", "draw", "drawing", "pulling", "current", "capacitor", "cap", "reads",
    "reading", "static", "manifold", "inlet", "outlet", "sensor", "thermocouple", "ohms", "insulation", "torque",
    "flow", "drop", "precharge", "amps", "line", "resistance", "carrying", "load",
}  # fmt: skip
UNIT_WORDS = sorted(set(UNITS) | {"microfarads", "microamps", "millivolts", "megohms", "inches"})
CORRECTION = re.compile(r"\b(no wait|no weight|no,|i mean|sorry|actually|correction|scratch that)\b", re.IGNORECASE)
COPULA = {"is", "reads", "reading", "at", "now", "was", "of", "s"}
APPROXIMATE = {"about", "around", "maybe", "roughly", "approximately", "like"}
NUMBER = re.compile(r"^\d+(\.\d+)?$")
GLUED = re.compile(r"^(\d+(?:\.\d+)?)([a-z]{1,6})$")  # "131c", "50mohms": a number with an unknown suffix
GLUED_AMPS = re.compile(r"^\d+a$")
TERMINAL = re.compile(r"^[lt][123]$")
RUN_NUMBER = re.compile(r"^\d+(\.\d+)?a?$")
RUN_PIECE = re.compile(r"^(\d+(\.\d+)?a?|[a-z]{1,3}\d?)$")  # "l1", "rla", "240", "60a"
ORDINALS = {"st", "nd", "rd", "th"}
SINGLE_CUES = {"sorry", "actually", "correction"}
PAIR_CUES = {("i", "mean"), ("scratch", "that")}
COUNT_BEFORE = {"unit", "circuit", "zone", "stage", "step", "number", "model", "part"}
COUNT_AFTER = {"ton", "tons", "wire", "wires", "of", "year", "years", "times"}  # not "am": it sounds like amps


@dataclass(frozen=True)
class Check:
    decision: str  # "accept" or "confirm"
    reading: Reading | None
    reason: str
    question: str


@dataclass(frozen=True)
class Settings:
    min_prob: float = 0.0
    window: int = 4  # tokens before a number searched for a measurement word
    unit_similarity: float = 0.8  # Jaro-Winkler on Metaphone keys for "sounds like a unit"


def _sounds_like_unit(token: str, th: Settings) -> bool:
    if token in UNITS or len(token) < 2:
        return False
    key = jellyfish.metaphone(token)
    return token.startswith("micro") or any(
        jellyfish.jaro_winkler_similarity(key, jellyfish.metaphone(u)) >= th.unit_similarity for u in UNIT_WORDS
    )


def _clause_has_number(tokens: list[str], start: int) -> bool:
    for t in tokens[start + 1 : start + 7]:
        if t in {"and", "but"}:
            return False
        if t[:1].isdigit():
            return True
    return False


def _word_prob(words: list[tuple[str, float]], value: str) -> float:
    parts = set(value.split("/"))
    probs = [p for w, p in words if re.sub(r"[^0-9.]", "", w).strip(".") in parts]
    return min(probs) if probs else 1.0


def _number_and_suffix(token: str) -> tuple[str, str] | None:
    """ "45" -> ("45", ""), "131c" -> ("131", "c"), anything else -> None."""
    if NUMBER.match(token):
        return token, ""
    glued = GLUED.match(token)
    return (glued.group(1), glued.group(2)) if glued else None


def _cue_at(tokens: list[str], i: int) -> bool:
    if i < len(tokens) and tokens[i] == "no":  # "no, 124" and "no wait" correct a value; "no leaks" does not
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        return nxt in ("wait", "weight") or bool(NUMBER.match(nxt))  # Whisper often writes "no weight"
    return (i < len(tokens) and tokens[i] in SINGLE_CUES) or tuple(tokens[i : i + 2]) in PAIR_CUES


def _glued_amps(pieces: list[str]) -> list[Check]:
    """ "60A" is amps, a model-number part or a refrigerant: confirm it, never accept it."""
    if not all(GLUED_AMPS.match(p) or TERMINAL.match(p) for p in pieces):
        return []  # part of a longer code
    values = [p[:-1] for p in pieces if GLUED_AMPS.match(p)]
    return [Check("confirm", Reading(v, "amps"), "unclear_unit", f"I heard {v} A. Is that {v} amps?") for v in values]


def _merged_numbers(pieces: list[str]) -> Check | None:
    """ "L1 L2 240" or "RLA 60A" merged like a code in a measuring line: ask rather than drop the number."""
    if len(pieces) < 2 or is_refrigerant("".join(pieces)) or not all(RUN_PIECE.match(p) for p in pieces):
        return None
    if not any(RUN_NUMBER.match(p) for p in pieces):
        return None
    return Check("confirm", None, "unclear_unit", f"I heard {' '.join(pieces)}. What was the reading, number and unit?")


def _is_count(tokens: list[str], i: int, end: int) -> bool:
    """ "unit 2", "3 ton", "step 2 of 5": numbers that are not measurements."""
    before = tokens[i - 1] if i > 0 else ""
    after = tokens[end + 1] if end + 1 < len(tokens) else ""
    return before in COUNT_BEFORE or after in COUNT_AFTER


def _unparsed_at(tokens: list[str], i: int, measuring: bool, th: Settings) -> Check | None:
    num = _number_and_suffix(tokens[i])
    if not num or num[1] in ORDINALS:
        return None
    value, suffix = num
    dual = None
    if not suffix and i + 2 < len(tokens) and tokens[i + 1] == "over":
        dual = _number_and_suffix(tokens[i + 2])  # "45 over 5 mft": a dual reading with no valid unit
    end = i + 2 if dual else i
    if dual:
        value, suffix = f"{value} over {dual[0]}", dual[1]
    nxt = suffix or (tokens[end + 1] if end + 1 < len(tokens) else "")
    near_label = any(w in LABELS for w in tokens[max(0, i - th.window) : i])
    sounds_like_unit = _sounds_like_unit(nxt, th)
    if (suffix and not dual and not (near_label or measuring)) or (not near_label and _is_count(tokens, i, end)):
        return None
    if not (dual or sounds_like_unit or ((near_label or measuring) and nxt not in UNITS)):
        return None
    heard = f"I heard {value}{f' {nxt}' if suffix or sounds_like_unit else ''}."
    if any(_cue_at(tokens, k) for k in range(max(0, i - 3), i)):
        return Check("confirm", None, "correction", f"You corrected yourself. {heard} What is the final reading?")
    return Check("confirm", None, "unclear_unit", f"{heard} What was the reading, number and unit?")


def unparsed_numbers(text: str, th: Settings, measuring: bool = False) -> list[Check]:
    """Numbers that look like measurements but did not parse as a reading. `measuring`: the caller knows the
    utterance answers a request for a reading."""
    tokens, groups = canonical_tokens(text), token_groups(text)
    spans = reading_spans(text)
    used = {k for a, b, _ in spans for k in range(a, b)}
    terminals = any(TERMINAL.match(piece) for g in groups for piece in g)  # L1, L2, T1: electrical legs and terminals
    # in a measuring line a bare number is likely a reading
    measuring = measuring or bool(spans) or terminals or any(t in LABELS for t in tokens)
    out = []
    for i in range(len(tokens)):
        if i in used or (i > 1 and tokens[i - 1] == "over" and _number_and_suffix(tokens[i - 2])):
            continue  # second half of a dual reading, handled with the first
        if _cue_at(tokens, i + 1) or _cue_at(tokens, i + 2):
            continue  # the value the speaker took back; the corrected one is checked instead
        model_part = i > 0 and tokens[i - 1] in COUNT_BEFORE
        amps = _glued_amps(groups[i]) if measuring and not model_part else []
        check = None if amps else _unparsed_at(tokens, i, measuring, th)
        check = check or (_merged_numbers(groups[i]) if measuring and not amps else None)
        out += amps + ([check] if check else [])
    return out


def labels_without_value(text: str) -> list[Check]:
    """A measurement word announced as a value ("superheat is ...") with no number in the same clause."""
    tokens = canonical_tokens(text)
    out = []
    for i, t in enumerate(tokens):
        announced = any(x in COPULA for x in tokens[i + 1 : i + 3])
        if t in LABELS and announced and not _clause_has_number(tokens, i):
            out.append(Check("confirm", None, "no_value", f"I didn't catch the {t} value. What was it?"))
    return out


def verify(
    text: str, words: list[tuple[str, float]], th: Settings, other: str | None = None, measuring: bool = False
) -> list[Check]:
    """One check per parsed reading, plus questions for measurements that did not parse."""
    tokens = canonical_tokens(text)
    other_readings = set(extract_readings(other)) if other is not None else None
    corrected = bool(CORRECTION.search(text))
    out = []
    for start, _, r in reading_spans(text):
        near = set(tokens[max(0, start - 3) : start])
        label = f"{r.value} {r.unit}"
        if corrected:
            out.append(Check("confirm", r, "correction", f"You corrected yourself. Is it {label}?"))
        elif near & APPROXIMATE:
            out.append(Check("confirm", r, "approximate", f"Is {label} the exact value?"))
        elif _word_prob(words, r.value) < th.min_prob:
            out.append(Check("confirm", r, "low_confidence", f"Did you say {label}?"))
        elif other_readings is not None and r not in other_readings:
            out.append(Check("confirm", r, "disagreement", f"Did you say {label}?"))
        else:
            out.append(Check("accept", r, "ok", ""))
    unparsed = unparsed_numbers(text, th, measuring)
    if corrected and not out and not any(c.reason == "correction" for c in unparsed):
        out.append(Check("confirm", None, "correction", "You corrected yourself. What is the final reading?"))
    if other_readings is not None:
        for r in other_readings - set(extract_readings(text)):
            out.append(Check("confirm", None, "disagreement", f"Did you also say {r.value} {r.unit}?"))
    return out + unparsed + labels_without_value(text)
