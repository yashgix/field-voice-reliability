"""The structured maintenance record, rebuilt from a visit's events, with the evidence behind every value."""

from collections import defaultdict
from datetime import datetime

from mvp.events import ClipStore, Event, EventLog
from mvp.visit import replay, spoken_values


def _traceable(events: list[Event], slot: str, value: str | None, by: str | None) -> bool:
    """A stored value was typed by the technician or said in one of this reading's recordings."""
    if value is None or by == "technician_typed":
        return True
    recordings = [e.data["transcript"] for e in events if e.kind == "utterance" and e.data["slot"] == slot]
    return any(value in spoken_values(t) for t in recordings)


def _evidence(events: list[Event], clips: ClipStore) -> dict[str, list[dict]]:
    out = defaultdict(list)
    for e in events:
        d = e.data
        if e.kind == "utterance":
            out[d["slot"]].append(
                {
                    "event": e.seq,
                    "purpose": d["purpose"],
                    "transcript": d["transcript"],
                    "problem": d["problem"],
                    "clip": d["clip"],
                    "clip_intact": clips.intact(d["clip"]),
                }
            )
        elif e.kind in ("question", "value_set", "unconfirmed", "skipped", "reopened"):
            out[d["slot"]].append({"event": e.seq, e.kind: d.get("text") or d.get("status") or d.get("reason") or ""})
    return out


def origin(status: str, by: str | None) -> str | None:
    """How the stored value was entered: accepted with no question, given by voice or tap after a question or a
    read-back correction, or typed."""
    if status not in ("accepted", "confirmed", "corrected"):
        return None
    return {"checker": "automatic", "technician_typed": "typed"}.get(by, "clarified")


def readback_decisions(events: list[Event]) -> list[dict]:
    """Every read-back decision in order: the value shown, confirmed or corrected, seconds from the moment that value
    was on screen, and whether its recording was played first."""
    out, shown_at, played = [], None, set()
    for e in events:
        if e.kind == "readback_shown":
            shown_at = e.ts
        elif e.kind == "audio_played":
            played.add(e.data["slot"])
        elif e.kind in ("value_checked", "reopened") and shown_at:
            slot, seconds = e.data["slot"], (datetime.fromisoformat(e.ts) - datetime.fromisoformat(shown_at))
            decision = "confirmed" if e.kind == "value_checked" else "corrected"
            shown = e.data.get("shown", {}).get("value")  # absent in logs written before the per-value read-back
            out.append(
                {
                    "slot": slot,
                    "shown": shown,
                    "decision": decision,
                    "seconds": round(seconds.total_seconds(), 1),
                    "listened": slot in played,
                }
            )
            played.discard(slot)
            # the next value appears at once; after a correction, timing restarts with the next read-back
            shown_at = e.ts if e.kind == "value_checked" else None
    return out


def _seeded_outcomes(events: list[Event], decisions: list[dict]) -> list[dict]:
    """Evaluation mode: whether each value planted at the first read-back was corrected (caught) or confirmed."""
    first = next((e for e in events if e.kind == "readback_shown"), None)
    if first is None:
        return []
    corrected = {d["slot"] for d in decisions if d["decision"] == "corrected"}
    return [dict(s, caught=s["slot"] in corrected) for s in first.data["seeded"]]


def build_record(log: EventLog, clips: ClipStore, visit_id: str) -> dict:
    events = log.events(visit_id)
    v = replay(events)
    evidence, decisions = _evidence(events, clips), readback_decisions(events)
    corrected = {d["slot"] for d in decisions if d["decision"] == "corrected"}
    readings = [
        {
            "key": s.key,
            "label": s.label,
            "value": s.value,
            "unit": s.unit,
            "status": s.status,
            "by": s.by,
            "origin": origin(s.status, s.by),
            "corrected_at_readback": s.key in corrected,
            "checked_at_readback": s.key in v.checked,
            "traceable": _traceable(events, s.key, s.value, s.by),
            "evidence": evidence[s.key],
        }
        for s in v.slots.values()
    ]
    broken_clips = sorted({x["clip"] for r in readings for x in r["evidence"] if "clip" in x and not x["clip_intact"]})
    return {
        "visit_id": visit_id,
        "job_id": v.job["id"],
        "versions": events[0].data["versions"],
        "evaluation": v.eval is not None,
        "complete": v.stage == "closed",
        "started": events[0].ts,
        "last_event": events[-1].ts,
        "readings": readings,
        "readback": {
            "rounds": sum(e.kind == "readback_shown" for e in events),
            "decisions": decisions,
            "seeded": _seeded_outcomes(events, decisions),
        },
        "audit": {
            "events": len(events),
            "chain_problems": log.verify(),
            "clips_missing_or_changed": broken_clips,
            "untraceable_values": [r["key"] for r in readings if not r["traceable"]],
        },
    }
