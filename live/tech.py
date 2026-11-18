"""Reply policy v2 for the simulated technician: plausible answers to reasonable questions, from the script only.

Fixed before any run that uses it. In order, after the scripted answer to an open ambiguity:
1. a model or serial question: the tech reads the plate of the unit asked about
2. a question that mentions a number from a recent reading: the tech restates that reading, corrected if it was
3. a question that names a field: the tech restates the latest recent reading of it, so a wrong guess gets corrected
4. a reading asked about that is no longer recent: "not sure, i'd have to measure that again"
5. anything else: "nothing to add"
Every reply is voiced and recognised like any other line.
"""

import random
import re

from fvr.synth import say_id, say_number
from live.entries import numbers, said, same
from live.scenario import Turn, Visit, truth

WINDOW = 3  # scripted lines a tech still remembers exactly
CANNOT = "not sure, i'd have to measure that again"
NOTHING = "nothing to add"
SPOKEN = {
    "suction_pressure": "suction pressure", "head_pressure": "head pressure", "superheat": "superheat",
    "subcooling": "subcooling", "supply_air_temp": "supply air", "return_air_temp": "return air",
    "delta_t": "delta t", "temp_rise": "temperature rise", "compressor_amps": "compressor amps",
    "condenser_fan_amps": "condenser fan amps", "blower_amps": "blower amps", "capacitor_uf": "capacitor microfarads",
    "line_voltage": "line voltage", "static_pressure": "static pressure", "gas_pressure": "gas pressure",
    "flame_sensor_ua": "flame sensor microamps", "insulation_resistance": "megohms",
}  # fmt: skip
PATTERNS = {
    "suction_pressure": r"suction", "head_pressure": r"\bhead", "superheat": r"super ?heat", "subcooling": r"sub ?cool",
    "supply_air_temp": r"supply", "return_air_temp": r"return", "delta_t": r"delta", "temp_rise": r"\brise",
    "compressor_amps": r"compressor", "condenser_fan_amps": r"\bfan", "blower_amps": r"blower",
    "capacitor_uf": r"\bcap|micro ?farad", "line_voltage": r"volt", "static_pressure": r"static",
    "gas_pressure": r"\bgas|manifold", "flame_sensor_ua": r"flame|micro ?amp", "insulation_resistance": r"meg",
}  # fmt: skip
PLATE = re.compile(r"model|serial|plate|tag", re.I)


def _say(value: str) -> str:
    decimals = len(value.split(".")[1]) if "." in value else 0
    return say_number(float(value), decimals, random.Random(value))


def spoken_field(name: str) -> str:
    base = name.removesuffix("_after")
    return SPOKEN[base] + (" after the repair" if base != name else "")


def restatement(name: str, value: str) -> str:
    lead = "hang on, let me measure again." if len(value) % 2 else "that's the"
    return f"{lead} {spoken_field(name)}, {_say(value)}"


def plate(name: str, value: str) -> str:
    return f"the plate says {name} {say_id(value, random.Random(value))}"


def possible(visit: Visit) -> list[str]:
    """Every v2 reply this visit can produce, so all of them can be voiced and recognised in advance."""
    out = [CANNOT]
    for t in visit.turns:
        for e in t.effects:
            if e["op"] in ("reading", "revise"):
                out.append(restatement(e["field"], str(e["value"])))
            if e["op"] == "ambiguous" and not isinstance(e["equip"], list):
                out.append(restatement(e["field"], str(e["resolves_to"])))
            if e["op"] == "equipment" and e["field"] in ("model", "serial"):
                out.append(plate(e["field"], str(e["value"])))
    for eq in visit.equipment:
        out += [plate("model", eq["model"]), plate("serial", eq["serial"])]
    return [*dict.fromkeys(out)]


def _asked_equip(ask: dict) -> set[str]:
    equip = ask.get("equip")
    return set(equip) if isinstance(equip, list) else {equip} if equip else set()


def _plate_reply(visit: Visit, state, ask: dict, text: str) -> str | None:
    if ask.get("field") not in ("model", "serial") and not PLATE.search(text):
        return None
    equip = _asked_equip(ask)
    if len(equip) != 1:
        return None
    eid = next(iter(equip))
    name = ask.get("field") if ask.get("field") in ("model", "serial") else ("serial" if "serial" in text else "model")
    listed = next((e[name] for e in visit.equipment if e["id"] == eid), None)
    value = state.equipment.get((eid, name), listed)
    return plate(name, value) if value else None


def _recent_keys(scripted: list[Turn]) -> list[tuple[str, str]]:
    """Reading keys set in the last few scripted lines, newest first."""
    keys = []
    for t in reversed(scripted[-WINDOW - 1 :]):
        keys += [(e["equip"], e["field"]) for e in t.effects if e["op"] in ("reading", "revise")]
    return keys


def _named_field(ask: dict, text: str) -> str | None:
    if ask.get("field") in SPOKEN or str(ask.get("field", "")).removesuffix("_after") in SPOKEN:
        return str(ask["field"])
    return next((f for f, p in PATTERNS.items() if re.search(p, text, re.I)), None)


def reply(visit: Visit, heard_so_far: list[Turn], ask: dict) -> str:
    """Policy v2 for a question that is not about an open ambiguity."""
    text = str(ask.get("question", ""))
    state = truth(heard_so_far)
    scripted = [t for t in heard_so_far if t.id.isdigit()]
    plate_text = _plate_reply(visit, state, ask, text)
    if plate_text:
        return plate_text
    recent = [k for k in _recent_keys(scripted) if k in state.readings]
    asked_numbers = numbers(text)
    for key in recent:
        if any(same(n, state.readings[key]) for n in asked_numbers) or any(
            said(v, text) for v in state.superseded.get(key, set())
        ):
            return restatement(key[1], state.readings[key])
    name = _named_field(ask, text)
    if name:
        equip = _asked_equip(ask)
        for key in recent:
            if key[1].removesuffix("_after") == name.removesuffix("_after") and (not equip or key[0] in equip):
                return restatement(key[1], state.readings[key])
        if any(f == name for _, f in state.readings):
            return CANNOT
    return NOTHING
