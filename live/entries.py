"""An arm's JSON record as comparable entries, plus value matching shared by the guards and the scorer."""

import re
from dataclasses import dataclass, field

from fvr.normalize import canonical_id, canonical_tokens
from live.scenario import EQUIPMENT_FIELDS, STATUSES, TASKS, is_reading_field


@dataclass
class Entries:
    readings: dict[tuple[str, str], str] = field(default_factory=dict)
    unresolved: set[tuple[tuple[str, ...], str]] = field(default_factory=set)
    work: dict[tuple[str, str], str] = field(default_factory=dict)
    equipment: dict[tuple[str, str], str] = field(default_factory=dict)
    evidence: dict[tuple[str, str], list[str]] = field(default_factory=dict)
    invalid: int = 0  # readings or work on unknown equipment, fields, tasks or statuses


def _equips(item: dict) -> tuple[str, ...]:
    e = item.get("equip")
    return tuple(str(x) for x in e) if isinstance(e, list) else (str(e),)


def normalize(record: dict | None, ids: set[str]) -> Entries:
    """Keep well-formed entries on known equipment, fields and tasks, and count the rest."""
    out = Entries()
    if not record:
        return out
    for r in record.get("readings") or []:
        equips, name = _equips(r), str(r.get("field"))
        if not (is_reading_field(name) and set(equips) <= ids):
            out.invalid += 1
            continue
        if r.get("status") == "unresolved" or len(equips) > 1:
            out.unresolved.add((equips, name))
        elif r.get("value") not in (None, ""):
            out.readings[(equips[0], name)] = str(r["value"])
            out.evidence[(equips[0], name)] = [str(x) for x in r.get("evidence") or []]
    for w in record.get("work") or []:
        key = (str(w.get("equip")), str(w.get("task")))
        if key[0] in ids and key[1] in TASKS and w.get("status") in STATUSES:
            out.work[key] = w["status"]
            out.evidence[key] = [str(x) for x in w.get("evidence") or []]
        else:
            out.invalid += 1
    for q in record.get("equipment") or []:
        key = (str(q.get("equip")), str(q.get("field")))
        if key[0] in ids and key[1] in EQUIPMENT_FIELDS and q.get("value"):
            out.equipment[key] = str(q["value"])
    return out


def _number(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def same(a: str, b: str) -> bool:
    x, y = _number(a), _number(b)
    if x is not None and y is not None:
        return abs(x - y) < 1e-6
    x, y = canonical_id(a), canonical_id(b)
    refrigerant = re.compile(r"r?\d{3}[a-z]?")
    if refrigerant.fullmatch(x) and refrigerant.fullmatch(y):  # "410A" and "R-410A"
        return x.removeprefix("r") == y.removeprefix("r")
    return x == y


def same_id(got: str, want: str) -> bool:
    """An identifier matches with or without the make in front ("Carrier 48TCED06")."""
    return same(got, want) or canonical_id(got).endswith(canonical_id(want))


def numbers(text: str) -> set[str]:
    """Numbers said in a line, including trade forms read as two numbers ("one eighteen" is 1, 18 and 118)."""
    text = re.sub(r"(\d) \.(\d)", r"\1.\2", text)  # Whisper writes "11 .2"
    tokens = [t for t in canonical_tokens(text) if _number(t) is not None]
    joined = {a + b for a, b in zip(tokens, tokens[1:], strict=False) if "." not in a}
    return set(tokens) | joined | set(re.findall(r"\d+(?:\.\d+)?", text))  # digits glued to letters ("T19")


def said(value: str, text: str) -> bool:
    return any(same(value, n) for n in numbers(text))
