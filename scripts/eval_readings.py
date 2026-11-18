"""Compare reading-reliability policies on every set with readings. Tunes only on split == "dev".

Policies: plain Whisper, job-context Whisper, simple rules, verifier (one decode), verifier with a second decode,
always confirm (read back every utterance). The record-match safeguard from the pilot does not touch readings in a
single-decode setup, so it equals job-context Whisper here and is reported as such.
Usage: python scripts/eval_readings.py            (tunes on dev, scores every set, writes results/readings_eval.md)
       python scripts/eval_readings.py --human    (frozen: settings from results/readings_settings.json, human set
                                                   only, writes results/human/eval.md; refuses once FROZEN.txt exists)
       python scripts/eval_readings.py --posthoc  (current code on the spent human set, writes
                                                   results/human-posthoc/eval.md; results/human stays frozen)
"""

import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from fvr.fields import Reading, extract_readings
from fvr.readings import Check, Settings, labels_without_value, unparsed_numbers, verify

ROOT = Path(__file__).resolve().parents[1]
SETS = {"synthetic": "results/synthetic", "readings": "results/readings", "human": "results/human"}
SYNTH_NOISES = {"clean", "ac_5", "ac_0", "babble_5"}
POLICIES = ["plain", "context", "rules", "verifier", "verifier_2", "always_confirm"]
PROBS = [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]


def truths(row: dict) -> list[dict]:
    if "truth" in row:
        return row["truth"]
    return [{"value": v, "unit": u, "unit_spoken": True, "ask": False} for v, u in row["readings"]]


def load(folder: Path) -> list[dict]:
    if not (folder / "decodes.jsonl").exists():
        return []
    dec = defaultdict(dict)
    for line in (folder / "decodes.jsonl").open():
        d = json.loads(line)
        dec[(d["utt_id"], d["noise"])][d["condition"]] = d
    rows = []
    for line in (folder / "manifest.jsonl").open():
        r = json.loads(line)
        ds = dec.get((r["utt_id"], r["noise"]), {})
        if "none" in ds and "job" in ds and (r.get("noise") in SYNTH_NOISES or "truth" in r):
            r["decodes"] = ds
            if truths(r):
                rows.append(r)
    return rows


def checks_for(policy: str, row: dict, th: Settings) -> list[Check]:
    plain, ctx = row["decodes"]["none"], row["decodes"]["job"]
    if policy == "plain":
        return [Check("accept", r, "ok", "") for r in extract_readings(plain["text"])]
    if policy == "context":
        return [Check("accept", r, "ok", "") for r in extract_readings(ctx["text"])]
    if policy == "rules":
        accepted = [Check("accept", r, "ok", "") for r in extract_readings(ctx["text"])]
        return accepted + unparsed_numbers(ctx["text"], th) + labels_without_value(ctx["text"])
    if policy == "verifier":
        return verify(ctx["text"], ctx["words"], th)
    if policy == "verifier_2":
        return verify(ctx["text"], ctx["words"], th, other=plain["text"])
    if policy == "always_confirm":
        return [Check("confirm", r, "read_back", "") for r in extract_readings(ctx["text"])] + [
            Check("confirm", None, "read_back", "Anything else?")
        ]
    raise ValueError(policy)


def score(row: dict, checks: list[Check]) -> Counter:
    """Per-reading outcomes. Questions without a reading are matched to readings that never appeared."""
    pending = list(checks)
    read_back = any(x.reason == "read_back" for x in checks)
    c = Counter(truths=len(truths(row)), utts=1, asked_utt=int(any(x.decision == "confirm" for x in checks)))
    c["questions"] = sum(x.decision == "confirm" for x in checks)
    unmatched = []
    for t in truths(row):
        want = Reading(t["value"], t["unit"])
        hit = next((x for x in pending if x.reading == want), None)
        if hit:
            pending.remove(hit)
            if hit.decision == "accept":
                c["correct_accept"] += 1
            else:
                c["warranted_confirm" if t["ask"] else "false_alarm"] += 1
        else:
            unmatched.append(t)
    for t in unmatched:
        same = next(
            (x for x in pending if x.reading and (x.reading.unit == t["unit"] or x.reading.value == t["value"])), None
        )  # a misheard unit or a misheard number is one wrong reading, not a miss plus a spurious one
        if same:
            pending.remove(same)
            c["wrong_accept" if same.decision == "accept" else "wrong_confirm"] += 1
            continue
        question = next((x for x in pending if x.reading is None), None)
        if read_back:
            c["missing_flagged"] += 1  # a full read-back lets the technician notice every missing reading
        elif question:
            pending.remove(question)
            c["missing_flagged"] += 1
        else:
            c["missing_silent"] += 1
    for x in pending:
        if x.reading is not None:
            c["spurious_accept" if x.decision == "accept" else "spurious_confirm"] += 1
        elif x.reason != "read_back":
            c["false_alarm"] += 1
    return c


def summarise(c: Counter) -> dict:
    errors = sum(c[k] for k in ("wrong_accept", "wrong_confirm", "missing_flagged", "missing_silent",
                                "spurious_accept", "spurious_confirm"))  # fmt: skip
    caught = c["wrong_confirm"] + c["missing_flagged"] + c["spurious_confirm"]
    silent = c["wrong_accept"] + c["missing_silent"] + c["spurious_accept"]
    accepted = c["correct_accept"] + c["wrong_accept"] + c["spurious_accept"]
    return {
        "readings": c["truths"],
        "errors": errors,
        "silent_wrong": c["wrong_accept"] + c["spurious_accept"],
        "silent_missing": c["missing_silent"],
        "silent_rate": silent / max(1, c["truths"]),
        "caught": caught,
        "recall": caught / errors if errors else float("nan"),
        "false_alarms": c["false_alarm"],
        "precision": caught / (caught + c["false_alarm"]) if caught + c["false_alarm"] else float("nan"),
        "asked_utterances": c["asked_utt"] / max(1, c["utts"]),
        "questions_per_reading": c["questions"] / max(1, c["truths"]),
        "accepted_accuracy": c["correct_accept"] / accepted if accepted else float("nan"),
    }


def bootstrap_silent(per_utt: dict[str, Counter], n: int = 2000) -> tuple[float, float]:
    keys = sorted(per_utt)
    rng = random.Random(0)
    stats = []
    for _ in range(n):
        s = Counter()
        for _ in keys:
            s += per_utt[rng.choice(keys)]
        stats.append(summarise(s)["silent_rate"])
    stats.sort()
    return stats[int(0.025 * n)], stats[int(0.975 * n)]


def evaluate(rows: list[dict], policy: str, th: Settings) -> tuple[Counter, dict[str, Counter]]:
    total, per_utt = Counter(), defaultdict(Counter)
    for r in rows:
        c = score(r, checks_for(policy, r, th))
        total += c
        per_utt[r["utt_id"]] += c
    return total, per_utt


def tune(dev: list[dict]) -> Settings:
    """Pick the probability floor with the best caught-minus-false-alarms on dev (verifier policy)."""
    best = max(PROBS, key=lambda p: (lambda s: s["caught"] - s["false_alarms"])(
        summarise(evaluate(dev, "verifier", Settings(min_prob=p))[0])))  # fmt: skip
    return Settings(min_prob=best)


def table(rows: list[dict], th: Settings, title: str) -> list[str]:
    out = [f"\n### {title}: {len({r['utt_id'] for r in rows})} utterances, {sum(len(truths(r)) for r in rows)} "
           "readings (all noise conditions)\n",
           "| Policy | Silent errors (95% CI) | silent wrong | silent missing | Caught / errors | Recall | Precision | "
           "False alarms | Utterances interrupted | Questions per reading | Accepted accuracy | Extra latency |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]  # fmt: skip
    for p in POLICIES:
        start = time.perf_counter()
        total, per_utt = evaluate(rows, p, th)
        check_ms = 1000 * (time.perf_counter() - start) / max(1, len(rows))
        s = summarise(total)
        lo, hi = bootstrap_silent(per_utt)
        latency = "+1 decode (~1 s)" if p == "verifier_2" else f"{check_ms:.1f} ms"
        out.append(
            f"| {p} | {100 * s['silent_rate']:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}] | {s['silent_wrong']} | "
            f"{s['silent_missing']} | {s['caught']}/{s['errors']} | {100 * s['recall']:.0f}% | "
            f"{100 * s['precision']:.0f}% | {s['false_alarms']} | {100 * s['asked_utterances']:.0f}% | "
            f"{s['questions_per_reading']:.2f} | {100 * s['accepted_accuracy']:.1f}% | {latency} |"
        )
    return out


def human_main(posthoc: bool) -> None:
    """Human set scored with saved settings; nothing is tuned or chosen here."""
    if not posthoc and (ROOT / "results/human/FROZEN.txt").exists():
        sys.exit("results/human holds the frozen evaluation and is never rewritten; use --posthoc")
    th = Settings(**json.loads((ROOT / "results/readings_settings.json").read_text()))
    rows = load(ROOT / SETS["human"])
    if not rows:
        sys.exit("No decoded human recordings found in results/human")
    title, label, out = (
        ("Human set, post hoc (development data, not held out)", "human (Yash, post hoc)", "results/human-posthoc")
        if posthoc
        else ("Held-out human evaluation (frozen)", "human (Yash, held out)", "results/human")
    )
    lines = [f"# {title}", "", f"Settings loaded from results/readings_settings.json: {th}."]
    lines += table(rows, th, label)
    spoken = [r for r in rows if all(t["unit_spoken"] for t in truths(r))]
    lines += table(spoken, th, f"{label}, only lines where every unit was spoken") if posthoc else []
    for noise in sorted({r["noise"] for r in rows}):
        lines += table([r for r in rows if r["noise"] == noise], th, f"{label}, {noise}")
    (ROOT / out).mkdir(exist_ok=True)
    (ROOT / out / "eval.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main() -> None:
    data = {name: load(ROOT / path) for name, path in SETS.items() if name != "human"}
    dev = [r for name in ("synthetic", "readings") for r in data[name] if r.get("split") == "dev"]
    th = tune(dev)
    lines = [
        "# Reading reliability: policies compared",
        "",
        f"Probability floor tuned on dev only: {th.min_prob} ({len(dev)} dev rows from the two synthetic sets).",
        "Synthetic sets are TTS voices (labelled synthetic). The human set is scored separately (--human, --posthoc).",
        "The rules were written after reading the synthetic (v1) test failures, so that table is optimistic.",
        "Rule changes after the frozen human evaluation came from human-set failures, not from these sets.",
    ]
    for name, rows in data.items():
        test = [r for r in rows if r.get("split", "test") == "test"]
        if test:
            lines += table(test, th, f"{name} (test)")
            spoken = [r for r in test if all(t["unit_spoken"] for t in truths(r))]
            if len(spoken) < len(test):
                lines += table(spoken, th, f"{name} (test, only lines where every unit was spoken)")
    lines += table(dev, th, "dev (both synthetic sets, used for tuning)")
    (ROOT / "results/readings_eval.md").write_text("\n".join(lines) + "\n")
    (ROOT / "results/readings_settings.json").write_text(json.dumps({"min_prob": th.min_prob}) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    if "--human" in sys.argv or "--posthoc" in sys.argv:
        human_main(posthoc="--posthoc" in sys.argv)
    else:
        main()
