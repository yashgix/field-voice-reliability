"""Deterministic extraction of the critical fields a job record cares about: equipment IDs and readings."""

from dataclasses import dataclass
from decimal import Decimal

from fvr.normalize import UNITS, canonical_tokens, id_runs, is_refrigerant

_MULTIWORD_UNITS = {
    ("inches", "of", "water", "column"): "inches_wc",
    ("inches", "water", "column"): "inches_wc",
    ("micro", "amps"): "microamps",
    ("milli", "volts"): "millivolts",
    ("mega", "ohms"): "megohms",
    ("gallons", "a", "minute"): "gpm",
    ("gallons", "per", "minute"): "gpm",
    ("inch", "pounds"): "inch_pounds",
}


@dataclass(frozen=True)
class Reading:
    value: str
    unit: str


def _is_number(token: str) -> bool:
    try:
        float(token)
        return True
    except ValueError:
        return False


def norm_value(token: str) -> str:
    """Exact decimal text: "0.720" -> "0.72", "1500000" stays as is."""
    value = Decimal(token).normalize()
    return f"{value:f}"


def extract_id_runs(text: str) -> list[str]:
    """Identifier-looking runs, as space-joined pieces, so later matching can use whole tokens."""
    out = []
    for run in id_runs(text):
        t = "".join(run)
        if any(c.isalpha() for c in t) and len(t) >= 5 and not is_refrigerant(t):
            out.append(" ".join(run))
    return out


def extract_ids(text: str) -> list[str]:
    """Merged tokens with letters and digits, long enough to be a model or serial number."""
    return [r.replace(" ", "") for r in extract_id_runs(text)]


def _unit_at(tokens: list[str], i: int) -> tuple[str, int] | None:
    for words, unit in _MULTIWORD_UNITS.items():
        if tuple(tokens[i : i + len(words)]) == words:
            return unit, len(words)
    if i < len(tokens) and tokens[i] in UNITS:
        return UNITS[tokens[i]], 1
    return None


def reading_spans(text: str) -> list[tuple[int, int, Reading]]:
    """Numbers followed by a unit, with the canonical-token span each came from. "45 over 5 microfarads" is one."""
    tokens = canonical_tokens(text)
    out, i = [], 0
    while i < len(tokens):
        if not _is_number(tokens[i]):
            i += 1
            continue
        value, j = norm_value(tokens[i]), i + 1
        if j + 1 < len(tokens) and tokens[j] in ("over", "/") and _is_number(tokens[j + 1]):
            value, j = f"{value}/{norm_value(tokens[j + 1])}", j + 2
        unit = _unit_at(tokens, j)
        if unit:
            out.append((i, j + unit[1], Reading(value, unit[0])))
            i = j + unit[1]
        else:
            i += 1
    return out


def extract_readings(text: str) -> list[Reading]:
    return [r for _, _, r in reading_spans(text)]
