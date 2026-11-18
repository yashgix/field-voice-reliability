"""Visit scripts (see SPEC.md): loading, checking, and the true record after any line."""

import json
from dataclasses import dataclass, field
from pathlib import Path

FIELDS = {
    "suction_pressure": "psi", "head_pressure": "psi", "superheat": "F", "subcooling": "F", "supply_air_temp": "F",
    "return_air_temp": "F", "delta_t": "F", "temp_rise": "F", "compressor_amps": "A", "condenser_fan_amps": "A",
    "blower_amps": "A", "capacitor_uf": "uF", "line_voltage": "V", "static_pressure": "in_wc", "gas_pressure": "in_wc",
    "flame_sensor_ua": "uA", "insulation_resistance": "Mohm",
}  # fmt: skip
TASKS = {
    "replace_capacitor", "replace_contactor", "replace_compressor", "replace_fan_motor", "replace_blower_motor",
    "replace_filter", "clean_coil", "clean_flame_sensor", "add_refrigerant", "leak_search", "replace_thermostat",
    "clear_drain",
}  # fmt: skip
STATUSES = {"proposed", "approved", "declined", "in_progress", "done", "deferred"}
EQUIPMENT_FIELDS = {"model", "serial", "refrigerant"}
OPS = {"reading", "revise", "reassign", "retract", "work", "equipment", "ambiguous"}  # plus "resolve", internal only


@dataclass
class Turn:
    id: str
    speaker: str
    text: str
    effects: list[dict] = field(default_factory=list)


@dataclass
class Visit:
    id: str
    kind: str
    equipment: list[dict]
    turns: list[Turn]

    @property
    def equipment_ids(self) -> set[str]:
        return {e["id"] for e in self.equipment}

    @property
    def listed(self) -> dict[tuple[str, str], str]:
        """Model and serial from the equipment list, so a record repeating them is not counted as a new fact."""
        return {(e["id"], f): e[f] for e in self.equipment for f in ("model", "serial")}


@dataclass(frozen=True)
class Unresolved:
    """A value or an equipment the words cannot settle, from an `ambiguous` effect."""

    equip: tuple[str, ...]
    field: str
    options: tuple[str, ...]
    turn: str


@dataclass
class State:
    readings: dict[tuple[str, str], str] = field(default_factory=dict)
    superseded: dict[tuple[str, str], set[str]] = field(default_factory=dict)  # values later revised or moved
    work: dict[tuple[str, str], str] = field(default_factory=dict)
    earlier_status: dict[tuple[str, str], set[str]] = field(default_factory=dict)
    equipment: dict[tuple[str, str], str] = field(default_factory=dict)
    unresolved: dict[tuple[tuple[str, ...], str], Unresolved] = field(default_factory=dict)


def is_reading_field(name: str) -> bool:
    return name.removesuffix("_after") in FIELDS


def _check_effect(e: dict, ids: set[str], where: str) -> None:
    op = e.get("op")
    if op not in OPS:
        raise ValueError(f"{where}: unknown op {op!r}")
    if op == "reassign":
        equips = [e["from"], e["to"]]
    else:
        equips = e["equip"] if isinstance(e["equip"], list) else [e["equip"]]
    if any(x not in ids for x in equips):
        raise ValueError(f"{where}: unknown equipment in {e}")
    if op == "work" and (e["task"] not in TASKS or e["status"] not in STATUSES):
        raise ValueError(f"{where}: unknown task or status in {e}")
    if op == "equipment" and e["field"] not in EQUIPMENT_FIELDS:
        raise ValueError(f"{where}: unknown equipment field in {e}")
    if op == "ambiguous" and "resolves_to" not in e:
        raise ValueError(f"{where}: ambiguous effect without resolves_to in {e}")
    if op in ("reading", "revise", "reassign", "retract", "ambiguous") and not is_reading_field(e["field"]):
        raise ValueError(f"{where}: unknown reading field in {e}")


def load(path: Path | str) -> Visit:
    raw = json.loads(Path(path).read_text())
    ids = {e["id"] for e in raw["equipment"]}
    turns = []
    for t in raw["turns"]:
        for e in t.get("effects", []):
            _check_effect(e, ids, f"{raw['id']} turn {t['id']}")
        turns.append(Turn(str(t["id"]), t["speaker"], t["text"], t.get("effects", [])))
    return Visit(raw["id"], raw["kind"], raw["equipment"], turns)


def _move(state: State, key: tuple[str, str], value: str | None) -> None:
    """Set or clear a reading, remembering the value it replaces so a stale copy can be recognised."""
    old = state.readings.pop(key, None)
    if old is not None and old != value:
        state.superseded.setdefault(key, set()).add(old)
    if value is not None:
        state.readings[key] = value


def apply(state: State, e: dict, turn: str) -> None:
    op = e["op"]
    if op in ("reading", "revise"):
        state.unresolved.pop(((e["equip"],), e["field"]), None)  # a later clear value settles an open ambiguity
        _move(state, (e["equip"], e["field"]), str(e["value"]))
    elif op == "reassign":
        value = state.readings.get((e["from"], e["field"]))
        _move(state, (e["from"], e["field"]), None)
        if value is not None:
            _move(state, (e["to"], e["field"]), value)
    elif op == "retract":  # a withdrawn reading also withdraws an open question about it
        state.unresolved.pop(((e["equip"],), e["field"]), None)
        _move(state, (e["equip"], e["field"]), None)
    elif op == "work":
        key = (e["equip"], e["task"])
        if key in state.work:
            state.earlier_status.setdefault(key, set()).add(state.work[key])
        state.work[key] = e["status"]
    elif op == "equipment":
        key, old = (e["equip"], e["field"]), state.equipment.get((e["equip"], e["field"]))
        if old is not None and old != str(e["value"]):
            state.superseded.setdefault(key, set()).add(old)
        state.equipment[key] = str(e["value"])
    elif op == "ambiguous":
        equip = tuple(e["equip"]) if isinstance(e["equip"], list) else (e["equip"],)
        options = tuple(str(o) for o in e.get("options") or [e["value"]])
        state.unresolved[(equip, e["field"])] = Unresolved(equip, e["field"], options, turn)
        if len(equip) == 1:  # a new, unsettled value replaces the old one. An unsettled owner leaves others alone
            _move(state, (equip[0], e["field"]), None)
    elif op == "resolve":
        u = state.unresolved.pop((tuple(e["equip"]), e["field"]))
        if len(u.equip) > 1:
            _move(state, (e["to"], u.field), u.options[0])
        else:
            _move(state, (u.equip[0], u.field), str(e["value"]))


def truth(turns: list[Turn]) -> State:
    """The true record after the given lines, in order."""
    state = State()
    for t in turns:
        for e in t.effects:
            apply(state, e, t.id)
    return state


REPLY = "reply:"  # key prefix for rendered replies, which have no fixed line id


def spoken(t: Turn, heard: dict[str, str]) -> str:
    """What the system heard for a line: its recognised text, a rendered reply, or the script text."""
    return heard.get(t.id) or heard.get(REPLY + t.text) or t.text


def answer_text(visit: Visit, effect: dict) -> str:
    """The scripted answer, or for a script that left it out, a fixed one built from the equipment list."""
    if effect.get("answer"):
        return effect["answer"]
    if isinstance(effect["equip"], list):
        e = next(x for x in visit.equipment if x["id"] == effect["resolves_to"])
        return f"that was the {e['type']} at the {e['location']}"
    return f"it was {effect['resolves_to']}"


def answer_turn(u: Unresolved, effect: dict, after: str, text: str) -> Turn:
    """The tech's answer when asked about an ambiguity, as a line inserted right after the question."""
    resolve = {"op": "resolve", "equip": list(u.equip), "field": u.field}
    if len(u.equip) > 1:
        resolve["to"] = effect["resolves_to"]
    else:
        resolve["value"] = str(effect["resolves_to"])
    return Turn(f"{after}a", "tech", text, [resolve])


def ambiguity_effect(visit: Visit, u: Unresolved) -> dict:
    turn = next(t for t in visit.turns if t.id == u.turn)

    def equips(e: dict) -> tuple[str, ...]:
        return tuple(e["equip"]) if isinstance(e["equip"], list) else (e["equip"],)

    return next(e for e in turn.effects if e["op"] == "ambiguous" and e["field"] == u.field and equips(e) == u.equip)
