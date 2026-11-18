"""The simple arms. All share one system prompt, one output schema and the same decision points.

A reads the finished visit once. A-live re-reads the visit so far after every spoken line. B does the same but also
sees its own record from the previous line, as a streaming agent with history does. R is A-live whose questions come
from a fixed rule instead of the model. Guards are applied afterwards (guards.py), so the +G arms reuse these calls.
"""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field

from live import tech
from live.entries import said
from live.scenario import (
    FIELDS,
    TASKS,
    Turn,
    Unresolved,
    Visit,
    ambiguity_effect,
    answer_text,
    answer_turn,
    spoken,
    truth,
)

ASK_WINDOW = 3  # scripted lines after an ambiguity during which the tech can still answer
UNPLANNED_ANSWER = "nothing to add"
REPEAT_REQUEST = re.compile(r"repeat|say (that|it) again|didn't catch|come again", re.I)
RULE_QUESTION = "sorry, can you repeat that?"
UNIT_QUESTION, VALUE_QUESTION = "which unit is that for?", "which value was it?"
ASKS_UNIT = re.compile(r"which (unit|one|equipment)", re.I)
ASKS_VALUE = re.compile(r"which (value|reading|number)", re.I)
UNNAMED = re.compile(r"\b(other one|next one|same as)\b", re.I)
POINTING = re.compile(r"\b(this|that|other|next) one\b", re.I)  # "one" here is not a number
BARE_SWITCH = re.compile(r"\b(next one|next unit|moving on|on to the next)\b", re.I)
EQUIPMENT_WORDS = re.compile(
    r"condenser|furnace|rooftop|heater|handler|split|heat pump|boiler|unit by|unit on|front|back|north|south|east|"
    r"west|left|right|upstairs|downstairs|attic|basement|roof|garage",
    re.I,
)
MEASURE_WORDS = re.compile(
    r"\b(suction|head|superheat|subcool|amp|volt|cap|static|gas|manifold|flame|pressure|supply|return|delta|compressor|"
    r"fan|blower)",
    re.I,
)
NUMBERISH = re.compile(r"\d|\b(zero|oh|one|two|three|four|five|six|seven|eight|nine|ten|twenty|thirty|forty|fifty|"
                       r"sixty|seventy|eighty|ninety|hundred|point)\b", re.I)  # fmt: skip

SYSTEM = f"""You keep the job record for an HVAC service visit from what is said during it.

Lines come from speech recognition and may contain errors. Speakers are not labelled, except lines the headset itself
said, marked (headset). The technician and the customer both talk. Numbers the customer mentions, setpoints and
prices are not readings.

Record:
- readings: the current value of each reading per equipment. Later corrections replace earlier values. A reading said
  to belong to other equipment moves there. A withdrawn reading is removed.
- work: the status of each task per equipment. proposed = suggested, approved = customer agreed, declined, deferred,
  in_progress = started but not finished, done = actually completed. Never mark done what was only proposed,
  approved or started. A removed part whose replacement is not installed is not done.
- equipment: model, serial or refrigerant facts said during the visit that differ from or add to the equipment list.
- If the words cannot settle a value, or which equipment it belongs to, do not guess. Add it with status
  "unresolved" and the candidate values in options (or a list of candidate equipment ids in equip).
- evidence: the ids of the lines that support each entry.
- ask: one short question to the technician, only when an answer now would settle an unresolved entry, as
  {{"equip": "E1", "field": "gas_pressure", "question": "..."}}. Otherwise null. Never repeat a question the headset
  already asked. If its answer did not settle the entry, leave it unresolved.

Reading fields: {", ".join(f"{k} ({v})" for k, v in FIELDS.items())}. Add _after for a re-measurement after a repair.
Work tasks: {", ".join(sorted(TASKS))}.

Reply with only this JSON, no other text:
{{"readings": [{{"equip": "E1", "field": "superheat", "value": "11", "status": "final", "options": [],
  "evidence": ["4"]}}],
 "work": [{{"equip": "E1", "task": "replace_filter", "status": "done", "evidence": ["7"]}}],
 "equipment": [{{"equip": "E1", "field": "model", "value": "GSX160361", "evidence": ["9"]}}],
 "ask": null}}
Values in readings are plain numbers in digits, without units."""


@dataclass
class Step:
    after: str
    raw: str
    record: dict | None
    reply: dict


@dataclass
class Run:
    arm: str
    visit: str
    turns: list[Turn]  # what this arm heard, including answers to its questions
    steps: list[Step] = field(default_factory=list)


Caller = Callable[[str, str], tuple[str, dict]]


def equipment_block(visit: Visit) -> str:
    rows = [
        f"{e['id']}: {e['type']}, {e['location']}, {e['make']} {e['model']}, serial {e['serial']}"
        for e in visit.equipment
    ]
    return "Equipment on site:\n" + "\n".join(rows)


def transcript_block(turns: list[Turn], heard: dict[str, str]) -> str:
    lines = [f"[{t.id}] {'(headset) ' if t.speaker == 'device' else ''}{spoken(t, heard)}" for t in turns]
    return "Lines so far:\n" + "\n".join(lines)


def parse_record(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, re.S)
    try:
        record = json.loads(match.group(0)) if match else None
    except json.JSONDecodeError:
        return None
    return record if isinstance(record, dict) else None


def record_prompt(visit: Visit, turns: list[Turn], heard: dict[str, str], note: str, previous: dict | None) -> str:
    parts = [equipment_block(visit), transcript_block(turns, heard)]
    if previous is not None:
        parts.append("Your record after the previous line:\n" + json.dumps(previous))
    parts.append(note)
    return "\n\n".join(parts)


def run_end(visit: Visit, heard: dict[str, str], ask_model: Caller) -> Run:
    note = "The visit is over. Write the final record. You cannot ask questions now, so ask is null."
    raw, meta = ask_model(SYSTEM, record_prompt(visit, visit.turns, heard, note, None))
    run = Run("A", visit.id, list(visit.turns))
    run.steps.append(Step(visit.turns[-1].id, raw, parse_record(raw), meta))
    return run


def _about(ask: dict, u: Unresolved) -> bool:
    """A structured question must name the field (and, if given, overlapping equipment). A plain question must
    mention a candidate value or the field."""
    if ask.get("field"):
        equip = ask.get("equip")
        asked = set(equip) if isinstance(equip, list) else {equip}
        return u.field == ask["field"] and (not equip or bool(asked & set(u.equip)))
    text = str(ask.get("question", ""))
    if ASKS_UNIT.search(text):
        return len(u.equip) > 1
    if ASKS_VALUE.search(text):
        return len(u.options) > 1
    return any(said(o, text) for o in u.options) or u.field.replace("_", " ") in text.lower()


def _scripted(t: Turn) -> bool:
    return t.id.isdigit()


def _asks_for(ask: dict, e: dict) -> bool:
    """A question names this reading: its field, and its equipment if the question gives one."""
    equip = ask.get("equip")
    asked = set(equip) if isinstance(equip, list) else {equip}
    return e["op"] in ("reading", "revise") and ask.get("field") == e["field"] and (not equip or e["equip"] in asked)


def _repeat(scripted: list[Turn], reply_id: str, wanted) -> Turn | None:
    """Repeat the latest recent line holding a reading that `wanted` accepts, as a tech would repeat a number."""
    for t in reversed(scripted[-ASK_WINDOW - 1 :]):
        if any(e["op"] in ("reading", "revise") and wanted(e) for e in t.effects):
            return Turn(reply_id, "tech", t.text)
    return None


def _answer(visit: Visit, heard_so_far: list[Turn], ask: dict | str, answered: set, policy: str = "v1") -> Turn:
    """The tech's reply to a question: the scripted answer if it is about a recent ambiguity, a repeat of the line if
    it asks for a recent reading or to repeat the last one, else a neutral reply."""
    ask = ask if isinstance(ask, dict) else {"question": str(ask)}
    scripted = [t for t in heard_so_far if _scripted(t)]
    ids, reply_id = [t.id for t in scripted], f"{heard_so_far[-2].id}a"
    for key, u in truth(heard_so_far).unresolved.items():
        if key not in answered and len(ids) - 1 - ids.index(u.turn) <= ASK_WINDOW and _about(ask, u):
            answered.add(key)
            effect = ambiguity_effect(visit, u)
            return answer_turn(u, effect, heard_so_far[-2].id, answer_text(visit, effect))
    if policy == "v2" and not REPEAT_REQUEST.search(str(ask.get("question", ""))):
        return Turn(reply_id, "tech", tech.reply(visit, heard_so_far, ask))
    if ask.get("field"):
        reply = _repeat(scripted, reply_id, lambda e: _asks_for(ask, e))
    elif REPEAT_REQUEST.search(str(ask.get("question", ""))):
        reply = _repeat(scripted[-1:], reply_id, lambda e: True)
    else:
        reply = None
    return reply or Turn(reply_id, "tech", UNPLANNED_ANSWER)


def _number_groups(text: str) -> int:
    """Separate numbers in a line: runs of number words or digits, split by commas and other words."""
    groups, inside = 0, False
    for word in re.sub(r"[,;]|\.\.\.", " | ", text).split():
        numeric = bool(NUMBERISH.fullmatch(word.strip(".~").lower()) or re.fullmatch(r"~?\.?\d+(\.\d+)?\.?", word))
        groups += numeric and not inside
        inside = numeric
    return groups


def rule_question(text: str, previous: str = "") -> str | None:
    """The fixed asking rule, in order: a repeat when a number was heard with low confidence or a measurement word
    came garbled with no number, which value when one measurement got two numbers, which unit when a number follows an
    unnamed switch or "the other one"."""
    numbers = POINTING.sub(" ", text)
    words = numbers.split()
    unsure_number = any(w.startswith("~") and NUMBERISH.search(w) for w in words)
    garbled_measure = (
        MEASURE_WORDS.search(text) and not NUMBERISH.search(numbers) and any(w.startswith("~") for w in words)
    )
    if unsure_number or garbled_measure:
        return RULE_QUESTION
    if len(MEASURE_WORDS.findall(text)) == 1 and _number_groups(numbers) >= 2:
        return VALUE_QUESTION
    after_bare_switch = BARE_SWITCH.search(previous) and not EQUIPMENT_WORDS.search(previous)
    if NUMBERISH.search(numbers) and (UNNAMED.search(text) or after_bare_switch):
        return UNIT_QUESTION
    return None


def _question(arm: str, record: dict | None, line: str, previous: str) -> dict | str | None:
    if arm == "R":
        return rule_question(line, previous)
    return record.get("ask") if record else None


def run_live(visit: Visit, heard: dict[str, str], ask_model: Caller, arm: str, policy: str = "v1") -> Run:
    """Decide after every line that is not the headset's own. B also sees its previous record. `policy` is how the
    tech replies: v1 (the first test runs), v2 (`tech.py`) or none (every question gets the neutral reply)."""
    run = Run(arm, visit.id, [])
    queue, answered, previous = list(visit.turns), set(), None
    note = "Write the full record as it stands now."
    while queue:
        turn = queue.pop(0)
        run.turns.append(turn)
        if turn.speaker == "device":
            continue
        raw, meta = ask_model(SYSTEM, record_prompt(visit, run.turns, heard, note, previous if arm == "B" else None))
        record = parse_record(raw)
        run.steps.append(Step(turn.id, raw, record, meta))
        if record is not None:
            previous = {k: v for k, v in record.items() if k != "ask"}
        before = [t for t in run.turns[:-1] if _scripted(t)]
        ask = _question(arm, record, spoken(turn, heard), spoken(before[-1], heard) if before else "")
        if ask and _scripted(turn):  # questions only after scripted lines, no loops
            question = Turn(f"{turn.id}q", "device", ask.get("question", "") if isinstance(ask, dict) else str(ask))
            reply = _answer(visit, [*run.turns, question], ask, answered, policy) if policy != "none" else None
            queue[:0] = [question, reply or Turn(f"{turn.id}a", "tech", UNPLANNED_ANSWER)]
    return run
