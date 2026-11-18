"""Tables for the synthetic set: context conditions, then arms with the safeguard (thresholds from dev only).

Usage: python scripts/analyze.py results/synthetic
"""

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

from fvr.arms import ARMS, run_arm
from fvr.metrics import (
    bootstrap_diff,
    context_insertions,
    fields_correct,
    safeguard_outcomes,
    silent_errors,
    term_hits,
    wer,
)
from fvr.normalize import canonical_id
from fvr.verify import Thresholds

CONDITIONS = ["none", "generic", "job", "stale", "wrong", "oracle"]
RECORDS = ["job", "stale", "wrong"]
MARGINS = [0, 2, 4, 6, 8, 10, 15, 20, 30]
MIN_PROBS = [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
NOISES = {"clean", "ac_5", "ac_0", "babble_5"}  # ac_10 was dropped mid-run to save time; its few rows are ignored


def load(folder: Path):
    rows = [json.loads(line) for line in (folder / "manifest.jsonl").open()]
    rows = [r for r in rows if r["noise"] in NOISES]
    decodes = defaultdict(dict)
    for line in (folder / "decodes.jsonl").open():
        d = json.loads(line)
        decodes[(d["utt_id"], d["noise"])][d["condition"]] = d
    arms = {}
    if (folder / "arms.jsonl").exists():
        arms = {json.loads(line)["key"]: json.loads(line) for line in (folder / "arms.jsonl").open()}
    return rows, decodes, arms


def pct(a: float, b: float) -> str:
    return f"{100 * a / b:.1f}%" if b else "n/a"


def condition_table(rows, decodes, noises) -> tuple[str, dict]:
    stats = defaultdict(Counter)
    paired = defaultdict(dict)
    for r in rows:
        if r["noise"] not in noises:
            continue
        ds = decodes.get((r["utt_id"], r["noise"]), {})
        if len(ds) < len(CONDITIONS):
            continue
        none_ok = fields_correct(r, ds["none"]["text"])
        for c in CONDITIONS:
            d = ds[c]
            s = stats[c]
            e, n = wer(r["ref_text"], d["text"])
            s["wer_err"] += e
            s["wer_n"] += n
            hits = term_hits(r["terms"], d["text"])
            s["term_miss"] += hits.count(False)
            s["terms"] += len(hits)
            ok = fields_correct(r, d["text"])
            kinds = ["id"] * len(r["ids"]) + ["reading"] * len(r["readings"])
            for kind, good, was in zip(kinds, ok, none_ok, strict=True):
                s[f"{kind}_n"] += 1
                s[f"{kind}_ok"] += good
                s["broke"] += was and not good
                s["fixed"] += good and not was
            s["utt_all_ok"] += all(ok)
            s["utts"] += 1
            if c in ("job", "stale", "wrong"):
                prompt = r["prompts"][c] or ""
                record_ids = [w.strip(".;,") for w in prompt.split() if any(ch.isdigit() for ch in w)]
                s["ctx_insert"] += context_insertions(r, d["text"], record_ids)
            s["sec"] += d["seconds"]
            key = f"{r['utt_id']}"
            prev = paired[c].get(key, (0.0, 0))
            paired[c][key] = (prev[0] + sum(ok) - sum(none_ok), prev[1] + len(ok))
    lines = [
        "| Condition | WER | Term misses | Model-number exact | Reading exact | All fields right | "
        "Broke vs none | Fixed vs none | Record IDs inserted | s/decode | Field accuracy vs none (95% CI) |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    out = {}
    for c in CONDITIONS:
        s = stats[c]
        diff = bootstrap_diff(paired[c]) if c != "none" else (0.0, 0.0, 0.0)
        out[c] = {k: v for k, v in s.items()}
        out[c]["diff_ci"] = diff
        lines.append(
            f"| {c} | {pct(s['wer_err'], s['wer_n'])} | {pct(s['term_miss'], s['terms'])} | "
            f"{pct(s['id_ok'], s['id_n'])} ({s['id_ok']}/{s['id_n']}) | {pct(s['reading_ok'], s['reading_n'])} "
            f"({s['reading_ok']}/{s['reading_n']}) | {pct(s['utt_all_ok'], s['utts'])} | {s['broke']} | {s['fixed']} | "
            f"{s['ctx_insert'] if c in RECORDS else '-'} | {s['sec'] / max(1, s['utts']):.2f} | "
            f"{'-' if c == 'none' else f'{100 * diff[0]:+.1f} pts [{100 * diff[1]:+.1f}, {100 * diff[2]:+.1f}]'} |"
        )
    return "\n".join(lines), out


def arm_counts(rows, decodes, arms, split, th_by_arm, noises=None):
    agg = defaultdict(Counter)
    secs = defaultdict(list)
    for r in rows:
        if r["split"] != split or (noises and r["noise"] not in noises):
            continue
        key = f"{r['utt_id']}|{r['noise']}"
        if key not in arms:
            continue
        ds = decodes[(r["utt_id"], r["noise"])]
        for cond in RECORDS:
            for arm in ARMS:
                res = run_arm(arm, ds, arms[key], cond, th_by_arm[arm])
                c = safeguard_outcomes(r, res.decisions)
                c["fields"] += len(r["ids"]) + len(r["readings"])
                c["text_fields_ok"] += sum(fields_correct(r, res.text))
                c["rewrote"] += res.rewrote
                c["rows"] += 1
                agg[(arm, cond)] += c
                secs[(arm, cond)].append(res.seconds)
    return agg, secs


def _auc(pos: list[float], neg: list[float]) -> float:
    if not pos or not neg:
        return float("nan")
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def gate_table(rows, decodes, arms) -> str:
    """Can the acoustic signals tell a context rewrite that fixes fields from one that breaks them?"""
    lines = [
        "| Split | Rewrites that fix fields | Rewrites that break fields | AUC, whole-transcript score gap | "
        "AUC, lowest prompt-free word probability among changed words |",
        "|---|---|---|---|---|",
    ]
    for split in ("dev", "test"):
        gap = {True: [], False: []}
        word = {True: [], False: []}
        for r in rows:
            key = f"{r['utt_id']}|{r['noise']}"
            if r["split"] != split or key not in arms:
                continue
            ev, ds = arms[key], decodes[(r["utt_id"], r["noise"])]
            base = sum(fields_correct(r, ds["none"]["text"]))
            base_words = {canonical_id(w) for w in ds["none"]["text"].split()}
            for cond in RECORDS:
                cands = [(ds[cond], ev[cond]["hybrid"]["lp_context"])]
                if ev[cond]["detect"]["items"]:
                    cands.append((ev[cond]["detect"]["redecode"], ev[cond]["detect"]["lp_redecode"]))
                for d, lp in cands:
                    now = sum(fields_correct(r, d["text"]))
                    if now == base:
                        continue
                    changed = [p for w, p in d["words"] if canonical_id(w) and canonical_id(w) not in base_words]
                    gap[now > base].append(lp - ev["lp_none"])
                    word[now > base].append(min(changed) if changed else 1.0)
        lines.append(
            f"| {split} | {len(gap[True])} | {len(gap[False])} | {_auc(gap[True], gap[False]):.2f} | "
            f"{_auc(word[True], word[False]):.2f} |"
        )
    return "\n".join(lines)


def objective(c: Counter) -> int:
    return silent_errors(c) + c["correct_confirm"]


def tune(rows, decodes, arms) -> dict:
    best = {}
    for arm in ARMS:
        scores = []
        for m in MARGINS:
            for p in MIN_PROBS:
                th = Thresholds(accept_margin=m, min_prob=p)
                agg, _ = arm_counts(rows, decodes, arms, "dev", {a: th for a in ARMS})
                total = sum((agg[(arm, c)] for c in RECORDS), Counter())
                scores.append((objective(total), m, p))
        _, m, p = min(scores)
        best[arm] = Thresholds(accept_margin=m, min_prob=p)
    return best


def arms_table(agg, secs) -> str:
    lines = [
        "| Arm | Record | Fields right in text | Silent errors | Caught (wrong, confirmed) | "
        "False alarms (right, confirmed) | Re-ask rate | Rewrites kept | Median s |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for cond in RECORDS:
        for arm in ARMS:
            c = agg[(arm, cond)]
            extracted = sum(v for k, v in c.items() if k.endswith(("_accept", "_confirm")))
            confirms = sum(v for k, v in c.items() if k.endswith("_confirm"))
            caught = c["wrong_confirm"] + c["spurious_confirm"]
            lines.append(
                f"| {arm} | {cond} | {pct(c['text_fields_ok'], c['fields'])} | {silent_errors(c)} "
                f"({pct(silent_errors(c), c['fields'])}) | {caught} | "
                f"{c['correct_confirm']} | {pct(confirms, extracted)} | {c['rewrote']} | "
                f"{statistics.median(secs[(arm, cond)]):.2f} |"
            )
    return "\n".join(lines)


def main(folder: Path) -> None:
    rows, decodes, arms = load(folder)
    test = [r for r in rows if r["split"] == "test"]
    noises = sorted({r["noise"] for r in rows})
    parts = [
        "# Synthetic set results (TTS voices, labelled synthetic)\n",
        f"Test split: {len({r['utt_id'] for r in test})} utterances x {len(noises)} noise conditions.\n",
        "## Context conditions, all noise levels pooled (test)\n",
    ]
    table, summary = condition_table(test, decodes, set(noises))
    parts.append(table)
    per_noise = {}
    for n in noises:
        t, s = condition_table(test, decodes, {n})
        per_noise[n] = s
        parts += [f"\n### Noise: {n}\n", t]
    result = {"conditions": summary, "per_noise": per_noise}
    if arms:
        best = tune(rows, decodes, arms)
        parts.append("\n## Arms with the safeguard (thresholds tuned on dev only)\n")
        parts.append(
            "Thresholds: "
            + ", ".join(f"{a}: margin {t.accept_margin}, min prob {t.min_prob}" for a, t in best.items())
            + "\n"
        )
        agg, secs = arm_counts(rows, decodes, arms, "test", best)
        parts.append(arms_table(agg, secs))
        for n in noises:
            agg_n, secs_n = arm_counts(rows, decodes, arms, "test", best, {n})
            parts += [f"\n### Arms, noise: {n}\n", arms_table(agg_n, secs_n)]
        parts += ["\n## Acoustic acceptance signals (0.5 = chance)\n", gate_table(rows, decodes, arms)]
        result["thresholds"] = {a: vars(t) for a, t in best.items()}
        result["arms"] = {f"{a}|{c}": dict(v) for (a, c), v in agg.items()}
    (folder / "tables.md").write_text("\n".join(parts) + "\n")
    (folder / "summary.json").write_text(json.dumps(result, indent=1, default=str))
    print("\n".join(parts))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
