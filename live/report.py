"""Score saved runs, add guarded variants (+G), print tables by condition and visit kind, and the headroom verdict.

Usage: python -m live.report RUN_DIR VISIT.json... [--arms A,A-live,B,R] [--disputed FILE] [--json OUT.json]
RUN_DIR holds run1/, run2/... with one folder per condition (gold, asr, asr-unhelpful).
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from live import tech
from live.arms import UNPLANNED_ANSWER
from live.entries import Entries, normalize, same
from live.guards import commit, guarded
from live.run import run_label
from live.scenario import Turn, Visit, load, spoken, truth
from live.score import Error, asr_lost, dropped, episodes, errors, heard_until, hedged, lagging, recall

AI_CAUSES = ("missing_clarification", "revision_status", "reference", "unsupported")
ASR_CAUSES = ("asr_lost", "asr_changed")
LIVE_ONLY = ("live_ai_errors", "live_asr_errors", *(f"live_{c}" for c in (*ASR_CAUSES, *AI_CAUSES)),
             "live_unsafe_done", "lag_points", "hedge_points", "dropped")  # fmt: skip
AUTHORS = {"c": "Claude helper", "g": "ChatGPT", "d": "dev"}
BAR, MARGIN = 10, 2  # headroom bar on AI-addressable live errors, and the band around it that is inconclusive


def _asr_outcome(final: Entries, state, turns: list[Turn], heard: dict[str, str] | None) -> dict[str, int]:
    """Final readings whose value the recognizer lost in every scripted line that said it, and what became of them."""
    scripted = [t for t in turns if t.id.isdigit()]
    lost = [k for k, v in state.readings.items() if heard is not None and asr_lost(k, v, scripted, heard)]
    recovered = sum(k in final.readings and same(final.readings[k], state.readings[k]) for k in lost)
    omitted = sum(k not in final.readings for k in lost)
    return {"asr_lost_values": len(lost), "recovered": recovered, "asr_omitted": omitted,
            "asr_corrupted": len(lost) - recovered - omitted}  # fmt: skip


def _score(steps: list[Entries], valid: list[bool], final: Entries, after: list[str], turns, listed, heard) -> dict:
    heard_so_far = [heard_until(turns, a) for a in after]
    truths = [truth(h) for h in heard_so_far]
    per_step = [errors(e, s, h, heard, listed) for e, s, h in zip(steps, truths, heard_so_far, strict=True)]
    pairs = zip(steps, steps[1:], truths[1:], valid, valid[1:], strict=False)
    return {
        "live": episodes(per_step),
        "final": errors(final, truths[-1], turns, heard, listed, final=True),
        "lag_points": sum(lagging(e, s) for e, s in zip(steps, truths, strict=True)),
        "hedge_points": sum(hedged(e, s) for e, s in zip(steps, truths, strict=True)),
        "dropped": sum(dropped(b, a, s) for b, a, s, vb, va in pairs if vb and va),
        "recall": recall(final, truths[-1], listed),
        **_asr_outcome(final, truths[-1], turns, heard),
    }


def _questions(turns: list[Turn], visit: Visit) -> dict[str, int]:
    lines = {t.text for t in turns if t.id.isdigit()}
    return {
        "questions": sum(t.id.endswith("q") for t in turns),
        "answered": sum(any(e["op"] == "resolve" for e in t.effects) for t in turns),
        "ambiguities": sum(e["op"] == "ambiguous" for t in visit.turns for e in t.effects),
        "repeated": sum(t.id.endswith("a") and t.text in lines for t in turns),
        "needless": sum(t.text == UNPLANNED_ANSWER for t in turns),
        "restated": sum(
            t.id.endswith("a") and t.text.startswith(("that's the", "hang on", "the plate")) for t in turns
        ),
        "cannot": sum(t.text == tech.CANNOT for t in turns),
    }


def _common(data: dict, visit: Visit, turns: list[Turn], valid: list[bool]) -> dict:
    return {
        "kind": visit.kind,
        "decisions": len(data["steps"]),
        "format_failures": valid.count(False),
        "input_tokens": sum(s["reply"]["input_tokens"] for s in data["steps"]),
        "output_tokens": sum(s["reply"]["output_tokens"] for s in data["steps"]),
        "seconds": [s["reply"]["seconds"] for s in data["steps"]],
        **_questions(turns, visit),
    }


def score_run(data: dict, visit: Visit) -> dict[str, dict]:
    """Scores for this arm and, for live arms, its guarded variant."""
    turns = [Turn(**t) for t in data["turns"]]
    listed = visit.listed
    heard = data["heard"] if data["condition"] == "asr" else None
    steps = [normalize(s["record"], visit.equipment_ids) for s in data["steps"]]
    valid = [s["record"] is not None for s in data["steps"]]
    after = [s["after"] for s in data["steps"]]
    common = _common(data, visit, turns, valid)
    arm = data["arm"]
    out = {
        arm: {
            **common,
            "off_schema": sum(e.invalid for e in steps),
            **_score(steps, valid, steps[-1], after, turns, listed, heard),
        }
    }
    if arm != "A":
        texts = [{t.id: spoken(t, heard or {}) for t in heard_until(turns, a)} for a in after]
        committed = guarded(steps, texts)
        before_last = committed[-2] if len(committed) > 1 else Entries()
        final = commit(steps[-1], steps[-1], before_last, texts[-1])  # close-out: the done hold is released
        out[arm + "+G"] = {**common, "off_schema": 0, **_score(committed, valid, final, after, turns, listed, heard)}
    return out


def _ai(row: dict) -> int:
    return sum(e.cause in AI_CAUSES for e in row["live"])


def _summary(arm: str, rows: list[dict]) -> dict:
    live = [e for r in rows for e in r["live"]]
    causes = Counter(e.cause for e in live)
    secs = sorted(s for r in rows for s in r["seconds"])
    total = lambda k: sum(r[k] for r in rows)  # noqa: E731
    out = {
        "visit_runs": len(rows),
        "decisions": total("decisions"),
        "live_ai_errors": sum(causes[c] for c in AI_CAUSES),
        "live_asr_errors": sum(causes[c] for c in ASR_CAUSES),
        **{f"live_{c}": causes[c] for c in (*ASR_CAUSES, *AI_CAUSES)},
        "live_unsafe_done": sum(e.unsafe_done for e in live),
        **{k: total(k) for k in ("lag_points", "hedge_points", "dropped", "off_schema")},
        "final_errors": sum(len(r["final"]) for r in rows),
        "completeness": f"{sum(r['recall'][0] for r in rows)}/{sum(r['recall'][1] for r in rows)}",
        **{k: total(k) for k in ("asr_lost_values", "recovered", "asr_omitted", "asr_corrupted")},
        **{k: total(k) for k in ("questions", "answered", "ambiguities", "repeated", "restated", "cannot", "needless")},
        "format_failures": total("format_failures"),
        "input_tokens": total("input_tokens"),
        "output_tokens": total("output_tokens"),
        "median_s": secs[len(secs) // 2] if secs else None,
    }
    if arm == "A":  # one decision at the end: live columns do not apply
        out.update(dict.fromkeys(LIVE_ONLY, "n/a"))
    return out


def _table(summaries: dict[str, dict]) -> str:
    cols = list(next(iter(summaries.values())))
    lines = ["| arm | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    lines += [f"| {arm} | " + " | ".join(str(s[c]) for c in cols) + " |" for arm, s in summaries.items()]
    return "\n".join(lines)


def _guard_effect(scored: dict, label: str, arm: str) -> tuple[int, int]:
    """Live errors the guards remove from an arm, and live errors they add."""
    removed = added = 0
    for (lab, name, visit, run), row in scored.items():
        guarded_row = scored.get((lab, arm + "+G", visit, run))
        if lab == label and name == arm and guarded_row:
            plain = {(e.key, e.kind, e.got) for e in row["live"]}
            kept = {(e.key, e.kind, e.got) for e in guarded_row["live"]}
            removed, added = removed + len(plain - kept), added + len(kept - plain)
    return removed, added


def _spread(rows: dict, arm: str, run: int) -> str:
    """How an arm's AI-addressable errors spread over visits and visit types, and its question burden."""
    mine = {k[2]: r for k, r in rows.items() if k[1] == arm and k[3] == run}
    hit = sorted(v for v, r in mine.items() if _ai(r))
    by_kind = Counter()
    for r in mine.values():
        by_kind[r["kind"]] += _ai(r)
    needless = sum(r["needless"] for r in mine.values())
    questions = sum(r["questions"] for r in mine.values())
    return (f"errors in {len(hit)} of {len(mine)} visits ({', '.join(hit) or 'none'}), by type "
            f"{dict(by_kind)}, {questions} questions of which {needless} needless")  # fmt: skip


def headroom(scored: dict, label: str = "asr") -> str:
    """AI-addressable live errors per visit and run, the best simple live arm per run with its spread, and an
    exploratory verdict."""
    rows = {k: r for k, r in scored.items() if k[0] == label and k[1] != "A"}
    arms = sorted({k[1] for k in rows})
    runs = sorted({k[3] for k in rows})
    visits = sorted({k[2] for k in rows})
    lines = ["| visit | run | " + " | ".join(arms) + " |", "|---" * (len(arms) + 2) + "|"]
    for v in visits:
        for r in runs:
            cells = [str(_ai(rows[(label, a, v, r)])) if (label, a, v, r) in rows else "-" for a in arms]
            lines.append(f"| {v} | {r} | " + " | ".join(cells) + " |")
    best = {r: min((sum(_ai(rows[k]) for k in rows if k[1] == a and k[3] == r), a) for a in arms) for r in runs}
    lines += [f"\nRun {r}: best simple arm {a} with {n}: {_spread(rows, a, r)}" for r, (n, a) in best.items()]
    totals = [n for n, _ in best.values()]
    if all(n >= BAR + MARGIN for n in totals):
        verdict = "HEADROOM: the best simple arm leaves enough AI-addressable errors in every run"
    elif all(n < BAR - MARGIN for n in totals):
        verdict = "NO HEADROOM: the best simple arm leaves too few AI-addressable errors in every run"
    else:
        verdict = f"INCONCLUSIVE: runs disagree or sit within {MARGIN} of the bar of {BAR}"
    return "\n".join(lines) + f"\nExploratory verdict ({label}): {verdict}. Read it with the spread and the questions."


def _plain(e: Error) -> dict:
    return {"key": list(e.key), "kind": e.kind, "got": e.got, "want": e.want, "cause": e.cause}


def _set_aside(row: dict, disputed: set) -> dict:
    """Move errors on disputed labels out of the counts into their own list."""
    out = {**row, "disputed": [e for k in ("live", "final") for e in row[k] if e.key in disputed]}
    for k in ("live", "final"):
        out[k] = [e for e in row[k] if e.key not in disputed]
    return out


def score_all(runs: Path, visits: dict[str, Visit], disputed: list[dict]) -> dict[tuple[str, str, str, int], dict]:
    scored = {}
    for f in sorted(runs.glob("run*/*/*.json")):
        data = json.loads(f.read_text())
        if data["visit"] in visits:
            label = run_label(data["condition"], data.get("asr_context"), data["replies"])
            keys = {tuple(d["key"]) for d in disputed if d["visit"] == data["visit"]}
            for arm, row in score_run(data, visits[data["visit"]]).items():
                scored[(label, arm, data["visit"], data["run"])] = _set_aside(row, keys)
    return scored


def missing(scored: dict, label: str, visits: list[str], arms: list[str]) -> list[str]:
    """Visit and arm pairs with no saved run for this condition: any of them makes the batch incomplete."""
    have = {(k[2], k[1]) for k in scored if k[0] == label}
    return [f"{v}/{a}" for v in visits for a in arms if (v, a) not in have]


def _groups(scored: dict, label: str) -> dict[str, dict[str, list[dict]]]:
    """Rows per arm for all visits, each visit type and each author."""
    out: dict[str, dict[str, list[dict]]] = {}
    for (lab, arm, visit, _), row in scored.items():
        if lab == label:
            for group in ("all", row["kind"], "by " + AUTHORS.get(visit[0], "other")):
                out.setdefault(group, {}).setdefault(arm, []).append(row)
    return out


def print_tables(scored: dict, visits: list[str], arms: list[str]) -> None:
    for label in sorted({k[0] for k in scored}):
        for group, by_arm in _groups(scored, label).items():
            print(f"\n### {label}, {group}\n\n" + _table({a: _summary(a, r) for a, r in by_arm.items()}))
        disputed = [(k, e) for k, r in scored.items() if k[0] == label for e in r["disputed"]]
        print(f"\n{label}: {len(disputed)} errors on disputed labels, not counted above")
        for (_, arm, visit, run), e in disputed:
            print(f"  {visit} run {run} {arm}: {e.kind} {list(e.key)} got {e.got}, author's label {e.want}")
        for arm in sorted({k[1] for k in scored if k[0] == label and k[1] != "A" and not k[1].endswith("+G")}):
            removed, added = _guard_effect(scored, label, arm)
            print(f"\n{label}: guards on {arm} removed {removed} live errors and added {added}")
        gaps = missing(scored, label, visits, arms)
        if gaps:
            print(f"\n### Headroom, {label}\n\nINCOMPLETE: no run for {', '.join(gaps)}. No verdict.")
        else:
            print(f"\n### Headroom, {label}\n\n" + headroom(scored, label))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("runs", type=Path)
    p.add_argument("visits", nargs="+", type=Path)
    p.add_argument("--arms", default="A,A-live,B,R")
    p.add_argument("--disputed", type=Path, help="JSON list of disputed labels to report apart")
    p.add_argument("--json", type=Path)
    a = p.parse_args()
    visits = {v.id: v for v in map(load, a.visits)}
    disputed = json.loads(a.disputed.read_text()) if a.disputed else []
    scored = score_all(a.runs, visits, disputed)
    print_tables(scored, sorted(visits), a.arms.split(","))
    if a.json:
        detail = {
            "/".join(map(str, k)): {kind: [_plain(e) for e in r[kind]] for kind in ("live", "final")}
            for k, r in scored.items()
        }
        a.json.write_text(json.dumps(detail, indent=1))


if __name__ == "__main__":
    main()
