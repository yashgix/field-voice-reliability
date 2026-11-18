"""Plain-code guards between what an arm proposes and what is committed to the live record.

1. Known equipment, fields, tasks and statuses only (done by `normalize`).
2. A reading is committed only if its value was said in one of the lines it cites. Otherwise the last committed value
   for that entry stays.
3. "done" is committed only after the arm has said done at two decision points in a row.
"""

from live.entries import Entries, said


def commit(proposed: Entries, previous_proposed: Entries, committed: Entries, texts: dict[str, str]) -> Entries:
    out = Entries(unresolved=set(proposed.unresolved), equipment=dict(proposed.equipment))
    for key, value in proposed.readings.items():
        cited = [texts[i] for i in proposed.evidence.get(key, []) if i in texts]
        if any(said(value, t.replace("~", "")) for t in cited):
            out.readings[key] = value
            out.evidence[key] = proposed.evidence[key]
        elif key in committed.readings:
            out.readings[key] = committed.readings[key]
            out.evidence[key] = committed.evidence.get(key, [])
    for key, status in proposed.work.items():
        if status == "done" and previous_proposed.work.get(key) != "done":
            if key in committed.work:
                out.work[key] = committed.work[key]
            continue
        out.work[key] = status
        out.evidence[key] = proposed.evidence.get(key, [])
    return out


def guarded(steps: list[Entries], texts: list[dict[str, str]]) -> list[Entries]:
    """The committed record after each decision point. `texts` holds, per decision point, the lines heard so far."""
    out, previous, committed = [], Entries(), Entries()
    for proposed, heard in zip(steps, texts, strict=True):
        committed = commit(proposed, previous, committed, heard)
        out.append(committed)
        previous = proposed
    return out
