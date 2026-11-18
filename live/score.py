"""Score an arm's records against the true record as of each decision point, and sort errors by cause.

Every check uses only the lines heard up to that decision point. Causes, checked in this order:
- asr_lost: a reading whose true value was said in a line that set it, but is missing from the recognised text
- asr_changed: a work status whose last setting line reads differently after recognition (a candidate, checked by
  hand)
- missing_clarification: the record states one of the candidates of an ambiguity that is still open
- revision_status: a value later corrected, moved or withdrawn, a re-measurement mixed up with the original, or a
  wrong work status
- reference: the value belongs to the same field on other equipment
- unsupported: anything else the truth does not hold (a value or task never said, or said too early)
"""

from dataclasses import dataclass

from fvr.normalize import canonical_tokens
from live.entries import Entries, said, same, same_id
from live.scenario import State, Turn, spoken

FORWARD = {"proposed": 0, "approved": 1, "in_progress": 2, "done": 3}


@dataclass(frozen=True)
class Error:
    key: tuple
    kind: str  # reading, work, equipment
    got: str
    want: str | None
    cause: str
    unsafe_done: bool = False


def _sets_reading(e: dict, key: tuple[str, str]) -> bool:
    if e["op"] in ("reading", "revise"):
        return (e["equip"], e["field"]) == key
    if e["op"] == "resolve":
        return e["field"] == key[1] and key[0] in (e.get("to"), *e["equip"])
    return False


def _heard_as(t: Turn, heard: dict[str, str]) -> str:
    return spoken(t, heard).replace("~", "")


def asr_lost(key, want: str, turns: list[Turn], heard: dict[str, str]) -> bool:
    spoken = [t for t in turns if any(_sets_reading(e, key) for e in t.effects) and said(want, t.text)]
    return bool(spoken) and not any(said(want, _heard_as(t, heard)) for t in spoken)


def _words(text: str) -> list[str]:
    return ["okay" if w == "ok" else w.removesuffix("'s") for w in canonical_tokens(text)]


def _asr_changed(key, turns: list[Turn], heard: dict[str, str]) -> bool:
    lines = [t for t in turns if any(e["op"] == "work" and (e["equip"], e["task"]) == key for e in t.effects)]
    return bool(lines) and _words(_heard_as(lines[-1], heard)) != _words(lines[-1].text)


def _open_candidate(key, got: str, state: State) -> bool:
    return any(
        key[0] in u.equip and key[1] == u.field and any(same(got, o) for o in u.options)
        for u in state.unresolved.values()
    )


def _stale(key, got: str, state: State) -> bool:
    if any(same(got, v) for v in state.superseded.get(key, set())):
        return True
    base = key[1].removesuffix("_after")  # a re-measurement after a repair written over the original, or the reverse
    return any(same(got, state.readings.get((key[0], f), "")) for f in (base, base + "_after") if f != key[1])


def _reading_cause(key, got: str, state: State, turns: list[Turn], heard: dict[str, str] | None) -> str:
    want = state.readings.get(key)
    if heard is not None and want is not None and asr_lost(key, want, turns, heard):
        return "asr_lost"
    if _open_candidate(key, got, state):
        return "missing_clarification"
    if _stale(key, got, state):
        return "revision_status"
    if any(same(got, v) for (e, f), v in state.readings.items() if f == key[1] and e != key[0]):
        return "reference"
    return "unsupported"


def _behind(key, got: str | None, state: State) -> bool:
    """Work shown at an earlier step of proposed, approved, in progress, done than it has reached: cautious."""
    want = state.work.get(key)
    if got not in FORWARD or want not in FORWARD:
        return False
    return FORWARD[got] < FORWARD[want] and got in state.earlier_status.get(key, set())


def lagging(rec: Entries, state: State) -> int:
    return sum(_behind(k, rec.work.get(k), state) for k in state.work)


def _work_cause(key, want: str | None, turns: list[Turn], heard: dict[str, str] | None) -> str:
    if heard is not None and _asr_changed(key, turns, heard):
        return "asr_changed"
    return "revision_status" if want else "unsupported"


def errors(
    rec: Entries,
    state: State,
    turns: list[Turn],
    heard: dict[str, str] | None,
    listed: dict[tuple[str, str], str],
    final: bool = False,
) -> list[Error]:
    """Entries the truth at this moment does not support, given the lines heard so far (`turns`). Missing entries
    and lagging work are not errors. Equipment facts are checked only in the final record."""
    out = []
    for key, got in rec.readings.items():
        want = state.readings.get(key)
        if want is None or not same(got, want):
            out.append(Error(key, "reading", got, want, _reading_cause(key, got, state, turns, heard)))
    for key, got in rec.work.items():
        want = state.work.get(key)
        if got != want and not _behind(key, got, state):
            out.append(Error(key, "work", got, want, _work_cause(key, want, turns, heard), got == "done"))
    for key, got in rec.equipment.items() if final else []:
        want = state.equipment.get(key) or listed.get(key)
        if want is not None and not same_id(got, want):
            cause = "revision_status" if _stale(key, got, state) else "unsupported"
            out.append(Error(key, "equipment", got, want, cause))
    return out


def hedged(rec: Entries, state: State) -> int:
    """Entries the record marks unsettled although the truth settled them and no ambiguity on them is open."""

    def open_on(equips, name) -> bool:
        return any(u.field == name and set(u.equip) & set(equips) for u in state.unresolved.values())

    return sum(
        not open_on(equips, name) and any((e, name) in state.readings for e in equips)
        for equips, name in rec.unresolved
    )


def recall(rec: Entries, state: State, listed: dict[tuple[str, str], str]) -> tuple[int, int]:
    """True entries the record holds correctly, out of all true entries. An open ambiguity counts if the record
    marks the same field on overlapping equipment unsettled. Facts that only repeat the equipment list are left out."""
    equipment = {k: v for k, v in state.equipment.items() if not (k in listed and same(v, listed[k]))}
    hits = sum(k in rec.readings and same(rec.readings[k], v) for k, v in state.readings.items())
    hits += sum(rec.work.get(k) == v for k, v in state.work.items())
    hits += sum(k in rec.equipment and same(rec.equipment[k], v) for k, v in equipment.items())
    hits += sum(
        any(name == u.field and set(equips) & set(u.equip) for equips, name in rec.unresolved)
        for u in state.unresolved.values()
    )
    return hits, len(state.readings) + len(state.work) + len(equipment) + len(state.unresolved)


def dropped(before: Entries, after: Entries, state: State) -> int:
    """True entries the record held at the previous decision point and no longer holds, though nothing changed them."""
    lost = sum(
        k in state.readings and same(v, state.readings[k]) and k not in after.readings
        for k, v in before.readings.items()
    )
    return lost + sum(state.work.get(k) == v and k not in after.work for k, v in before.work.items())


def episodes(per_step: list[list[Error]]) -> list[Error]:
    """One error per stretch of decision points in which the same entry stays wrong in the same way."""
    out, open_now = [], set()
    for errs in per_step:
        now = {(e.key, e.kind, e.got) for e in errs}
        out += [e for e in errs if (e.key, e.kind, e.got) not in open_now]
        open_now = now
    return out


def heard_until(turns: list[Turn], after: str) -> list[Turn]:
    index = next(i for i, t in enumerate(turns) if t.id == after)
    return turns[: index + 1]
