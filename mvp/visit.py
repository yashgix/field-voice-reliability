"""One visit, rebuilt from its events, and the pure decisions that move it forward.

Every value in a record comes from a reading the checker accepted, a value the technician confirmed or restated, or a
value the technician typed. Nothing is inferred from the job, filled in or corrected by the system.
"""

import re
from dataclasses import dataclass, field, replace

from fvr.fields import Reading, extract_readings, norm_value
from fvr.normalize import UNITS, canonical_tokens
from fvr.readings import NUMBER, Settings, verify
from mvp.events import Event

MAX_FAILED_ANSWERS = 2  # unusable answers per reading before it is stored as unconfirmed
YES = {"yes", "yeah", "yep", "yup", "correct", "right", "affirmative", "confirmed"}
NO = {"no", "nope", "nah", "wrong", "incorrect", "negative", "not"}
UNIT_NAMES = {
    "psi": "psi", "degrees": "degrees", "amps": "amps", "volts": "volts", "microfarads": "microfarads",
    "inches_wc": "inches of water column", "microamps": "microamps", "millivolts": "millivolts", "ohms": "ohms",
    "megohms": "megohms", "kilohms": "kilohms", "gpm": "gallons a minute", "percent": "percent",
    "inch_pounds": "inch pounds",
}  # fmt: skip
TYPED_VALUE = re.compile(r"^\d+(\.\d+)?(/\d+(\.\d+)?)?$")
LEADING_NUMBER = re.compile(r"^\d+(\.\d+)?")
UNIT_FRAGMENTS = {"m", "k", "u", "meg", "mega", "kilo", "milli", "micro"}
LEADING_NO = re.compile(
    r"^\W*(no|nope|nah)\b\W*", re.IGNORECASE
)  # "No, 58 amps" answers a question; not a self-correction


@dataclass
class Pending:
    kind: str  # "yesno" or "value"
    text: str
    proposed: Reading | None
    failed: int = 0


@dataclass
class Slot:
    key: str
    label: str
    units: list[str]
    status: str = "open"  # open, accepted, confirmed, corrected, unconfirmed, skipped
    value: str | None = None
    unit: str | None = None
    by: str | None = None
    clips: list[str] = field(default_factory=list)
    pending: Pending | None = None
    previous: Reading | None = None  # value before a read-back fix


@dataclass
class Visit:
    visit_id: str
    job: dict
    slots: dict[str, Slot]
    eval: dict | None = None
    stage: str = "capture"  # capture, missing, readback, closed
    readback: dict | None = None
    checked: set[str] = field(default_factory=set)  # values the technician confirmed one by one at read-back
    utt_ids: set[str] = field(default_factory=set)

    def pending_slot(self) -> Slot | None:
        return next((s for s in self.slots.values() if s.pending), None)

    def open_slots(self) -> list[Slot]:
        return [s for s in self.slots.values() if s.status == "open" and not s.pending]


@dataclass(frozen=True)
class Fill:
    reading: Reading


@dataclass(frozen=True)
class Ask:
    kind: str
    text: str
    proposed: Reading | None = None  # offered for a yes, or the value a "no" rejected
    failed: bool = True  # an unusable answer counts toward the limit; a clear "no" or a usable proposal does not


def describe(r: Reading) -> str:
    return f"{r.value.replace('/', ' over ')} {UNIT_NAMES.get(r.unit, r.unit)}"


def spoken_label(slot: Slot) -> str:
    """ "Suction pressure" -> "suction pressure" mid-sentence; "L2 current" keeps its capital."""
    first = slot.label.split()[0]
    return slot.label if first.isupper() or any(c.isdigit() for c in first) else slot.label[0].lower() + slot.label[1:]


def _reading(d: dict | None) -> Reading | None:
    return Reading(d["value"], d["unit"]) if d else None


def replay(events: list[Event]) -> Visit:
    first = events[0].data
    slots = {c["key"]: Slot(c["key"], c["label"], c["units"]) for c in first["job"]["checklist"]}
    v = Visit(events[0].visit_id, first["job"], slots, first.get("eval"))
    for e in events[1:]:
        d, s = e.data, slots.get(e.data.get("slot", ""))
        if e.kind == "utterance":
            v.utt_ids.add(d["utt_id"])
            s.clips.append(d["clip"])
        elif e.kind == "question":
            s.pending = Pending(d["kind"], d["text"], _reading(d["proposed"]), d["failed"])
        elif e.kind == "value_set":
            s.status, s.value, s.unit, s.by, s.pending = d["status"], d["value"], d["unit"], d["by"], None
        elif e.kind in ("unconfirmed", "skipped"):
            s.status, s.pending = e.kind, None
        elif e.kind == "reopened":
            if v.readback:  # a planted value stays on every read-back until its own reading is fixed
                v.readback = dict(v.readback, seeded=[x for x in v.readback["seeded"] if x["slot"] != s.key])
            s.previous = Reading(s.value, s.unit) if s.value else None
            s.status, s.value, s.unit, s.by, s.pending, v.stage = "open", None, None, None, None, "capture"
            v.checked.discard(s.key)  # a corrected value is checked again
        elif e.kind == "value_checked":
            v.checked.add(s.key)
        elif e.kind == "missing_shown":
            v.stage = "missing"
        elif e.kind == "readback_shown":
            v.stage, v.readback = "readback", d
        elif e.kind == "visit_closed":
            v.stage = "closed"
    return v


def spoken_values(text: str) -> set[str]:
    """Every value a transcript contains: parsed readings, bare numbers and numbers glued to a suffix ("39a")."""
    found = {m.group() for t in canonical_tokens(text) if (m := LEADING_NUMBER.match(t))}
    return found | {r.value for r in extract_readings(text)}


def _bare_number(text: str) -> str | None:
    """The transcript's only number, if it has exactly one in any form and no unit or unit fragment that did not
    parse. Proposing "35" for "35 over 5mft", or "5 ohms" for "5 m ohms", would drop part of the reading."""
    tokens = canonical_tokens(text)
    if any(t in UNITS or t in UNIT_FRAGMENTS or "ohm" in t for t in tokens):
        return None
    numbers = [t for t in tokens if LEADING_NUMBER.match(t)]
    return numbers[0] if len(numbers) == 1 and NUMBER.match(numbers[0]) else None


def judge_reading(text: str, words: list[tuple[str, float]], slot: Slot, th: Settings) -> Fill | Ask:
    """Accept one clean reading in the slot's unit, or ask one targeted question."""
    label = spoken_label(slot)
    if not text.strip():
        return Ask("value", f"I didn't catch that. Say the {label}, number and unit.")
    checks = verify(text, words, th, measuring=True)  # the app asked for this reading
    readings = [c for c in checks if c.reading is not None]
    others = [c for c in checks if c.reading is None]
    if len(readings) > 1:
        heard = " and ".join(describe(c.reading) for c in readings)
        return Ask("value", f"I heard {heard}. Say only the {label}, number and unit.")
    if not readings:
        bare = _bare_number(text)
        if bare and len(slot.units) == 1 and len(others) <= 1 and not any(c.reason == "correction" for c in others):
            proposed = Reading(bare, slot.units[0])  # proposed to the technician, never stored without a yes
            return Ask("yesno", f"I heard {bare}. Is that {describe(proposed)}?", proposed, failed=False)
        text_q = others[0].question if others else f"I didn't hear the {label}. Say it again, number and unit."
        return Ask("value", text_q)
    check, r = readings[0], readings[0].reading
    if r.unit not in slot.units:
        units = " or ".join(UNIT_NAMES.get(u, u) for u in slot.units)
        return Ask("value", f"I heard {describe(r)}, but {label} is in {units}. What was the reading?")
    if others:
        return Ask("value", f"I heard {describe(r)} and another number. Say only the {label}, number and unit.")
    if check.decision == "confirm":
        return Ask("yesno", check.question, r, failed=False)  # a usable answer that only needs a yes
    return Fill(r)


def yes_or_no(text: str) -> str:
    words = set(re.findall(r"[a-z']+", text.lower()))
    yes, no = bool(words & YES), bool(words & NO)
    return "yes" if yes and not no else "no" if no and not yes else "unclear"


def judge_answer(text: str, words: list[tuple[str, float]], slot: Slot, th: Settings) -> Fill | Ask:
    """An answer to the pending question. Only a clear yes stores the proposed value. A different value is checked
    like a new reading; "no", or repeating the proposed value with "no", asks for the value."""
    pending = slot.pending
    if pending.kind == "value":
        return judge_reading(text, words, slot, th)
    answer, proposed = yes_or_no(text), pending.proposed
    other_values = spoken_values(text) - {proposed.value, *proposed.value.split("/")}
    again = Ask("yesno", f"Please answer yes or no. {pending.text}", proposed)
    if other_values:
        return again if answer == "yes" else _counted(judge_reading(LEADING_NO.sub("", text), words, slot, th))
    if answer == "yes":
        return Fill(proposed)
    if answer == "no":
        return Ask("value", f"OK. What is the {spoken_label(slot)}, number and unit?", proposed, failed=False)
    return _counted(judge_reading(text, words, slot, th)) if spoken_values(text) else again


def _counted(outcome: Fill | Ask) -> Fill | Ask:
    """A yes or no question answered with another question's worth of input counts toward the retry limit, so
    switching between numbers cannot keep a reading open forever."""
    return replace(outcome, failed=True) if isinstance(outcome, Ask) else outcome


def fill_status(slot: Slot, r: Reading, answered: bool) -> str:
    if slot.previous is not None:
        return "confirmed" if r == slot.previous else "corrected"
    if not answered:
        return "accepted"
    proposed = slot.pending.proposed if slot.pending else None
    return "corrected" if proposed is not None and r != proposed else "confirmed"


def typed_reading(slot: Slot, value: str, unit: str) -> Reading | None:
    """A typed value in the parser's exact form ("11.0" is "11"), or None if it is not a number in a listed unit."""
    if not TYPED_VALUE.match(value) or unit not in slot.units:
        return None
    return Reading("/".join(norm_value(part) for part in value.split("/")), unit)


def seeded_errors(v: Visit) -> list[dict]:
    """Evaluation mode only: the wrong values scheduled for this job, shown at the first read-back on readings that
    hold a different value, and kept on later ones until that reading is fixed, to measure whether they are noticed."""
    if v.readback is not None:
        return v.readback["seeded"]
    planned = (v.eval or {}).get("schedule", [])
    stored = {k: s.value for k, s in v.slots.items()}
    return [dict(p, actual=stored[p["slot"]]) for p in planned if stored[p["slot"]] not in (None, p["shown"])]


def readback_items(v: Visit, seeded: list[dict]) -> list[dict]:
    shown = {s["slot"]: s["shown"] for s in seeded}
    return [
        {
            "slot": s.key,
            "label": s.label,
            "value": shown.get(s.key, s.value),
            "unit": s.unit,
            "status": s.status,
            "by": s.by,
        }
        for s in v.slots.values()
    ]


def next_check(v: Visit) -> dict | None:
    """The first read-back value the technician has not yet confirmed or corrected, in checklist order."""
    return next((it for it in v.readback["items"] if it["slot"] not in v.checked), None)


def spoken_item(it: dict) -> str:
    if it["value"]:
        return f"{it['label']}: {describe(Reading(it['value'], it['unit']))}."
    return f"{it['label']}: {'not confirmed' if it['status'] == 'unconfirmed' else 'not recorded'}."


def prompt(v: Visit) -> dict:
    """What the technician should be shown and told next."""
    if v.stage == "closed":
        return {"expect": "done", "say": "Visit saved."}
    pending = v.pending_slot()
    if pending:
        return {"expect": pending.pending.kind, "slot": pending.key, "say": pending.pending.text}
    if v.stage == "readback":
        item, items = next_check(v), v.readback["items"]
        position = items.index(item) + 1
        clips, say = v.slots[item["slot"]].clips, spoken_item(item)
        return {
            "expect": "readback",
            "item": item,
            "position": position,
            "total": len(items),
            "clips": clips,
            "say": say,
        }
    if v.stage == "missing":
        missing = [s.key for s in v.open_slots()]
        names = ", ".join(spoken_label(v.slots[k]) for k in missing)
        return {"expect": "missing", "missing": missing, "say": f"Still missing: {names}. Record them or skip."}
    slot = v.open_slots()[0]
    return {"expect": "reading", "slot": slot.key, "say": f"{slot.label}."}


def job_prompt(job: dict) -> str:
    """Recognition context from the job record only: trade, complaint, equipment. Never readings."""
    return f"Service call: {job['trade']}, {job['complaint']}. {'. '.join(job['equipment'])}."
