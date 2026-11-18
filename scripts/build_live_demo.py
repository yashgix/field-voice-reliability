"""Build the visit replay demo from saved runs: demo/live/index.html plus audio copied to demo/audio/live/.

Nothing is typed in by hand: lines, audio, the agent's record after every line, its questions and the tech's replies
come from the saved run files, and the checks against ground truth come from the scorer.

Usage: python scripts/build_live_demo.py
"""

import json
import shutil
from pathlib import Path

from live.entries import normalize, said, same
from live.render import replies
from live.scenario import FIELDS, REPLY, Turn, load, spoken
from live.scenario import truth as truth_of
from live.score import errors, heard_until, recall
from live.tech import spoken_field

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(json.loads((ROOT / "configs/pilot.json").read_text())["work_dir"]).expanduser() / "live"
OUT, AUDIO = ROOT / "demo/live", ROOT / "demo/audio/live"
CLEAN, NOISY = "results/live/stage1/run1/gold", "results/live/followup/run1/asr+job-v2"
VOICE = "results/live/voice/run1/voice-v2"
VISITS = [
    ("c01", CLEAN, "clean", "Ordinary tune-up",
     "Two units, clear speech. Readings become a structured record as they are spoken."),
    ("g04", CLEAN, "clean", "Two systems, four units",
     "A reading moved to another unit, a correction, a drain job reopened, a motor job approved but not done."),
    ("g03", CLEAN, "clean", "Three rooftop units",
     "An unclear reading asked about, a voltage moved to another unit, a serial corrected, a reading withdrawn."),
    ("g04", VOICE, "voice", "Same visit, a real voice",
     "The four-unit visit again, read aloud by a person in three takes: a quiet room, music playing, and an air duster "
     "going off. Whisper hears it with the job record as context. Answers to the agent's questions are simulated in "
     "the computer voice. Shown: the live record, which kept 5 of 9 facts. One read of the finished visit kept all 9. "
     "Live mode, fed the same recordings, kept 6 of 9 (see Results)."),
    ("c01", NOISY, "noisy", "Failure case: heavy noise",
     "The ordinary visit again with people talking at 0 dB, heard through Whisper with the job record as context. "
     "Some words never come through. The agent asks, and does not guess."),
]  # fmt: skip
MOMENTS = {"revise": "Correction", "reassign": "Reading moved to another unit", "retract": "Reading withdrawn",
           "ambiguous": "Unclear reading", "equipment": "Nameplate fact"}  # fmt: skip
STATUS_MOMENTS = {"approved": "Customer approves", "done": "Work done", "deferred": "Work deferred",
                  "declined": "Work declined"}  # fmt: skip
UNITS = {"psi": "psi", "F": "°F", "A": "A", "uF": "µF", "V": "V", "in_wc": "in. w.c.", "uA": "µA", "Mohm": "MΩ"}


def field_label(name: str) -> tuple[str, str]:
    return spoken_field(name).replace("capacitor microfarads", "capacitor"), UNITS[FIELDS[name.removesuffix("_after")]]


def moments(visit, turns: list[Turn], heard: dict, listed: dict) -> list[dict]:
    """Key moments from the script's own effects, plus, in noisy audio, lost readings and the agent's questions."""
    out, seen = [], {}
    for t in turns:
        if heard and t.id.endswith("q"):
            out.append({"line": t.id, "label": "Agent asks"})
        if heard and any(
            e["op"] in ("reading", "revise")
            and said(str(e["value"]), t.text)
            and not said(str(e["value"]), spoken(t, heard).replace("~", ""))
            for e in t.effects
        ):
            out.append({"line": t.id, "label": "Lost in noise"})
        for e in t.effects:
            if e["op"] == "equipment" and same(str(e["value"]), listed.get((e["equip"], e["field"]), "")):
                continue
            label = MOMENTS.get(e["op"])
            if e["op"] == "work":
                key = (e["equip"], e["task"])
                label = (
                    "Work reopened"
                    if seen.get(key) == "done" and e["status"] != "done"
                    else STATUS_MOMENTS.get(e["status"])
                )
                seen[key] = e["status"]
            if label and {"line": t.id, "label": label} not in out:
                out.append({"line": t.id, "label": label})
    return out


def final_summary(rec, state, turns: list[Turn], heard: dict, listed: dict) -> dict:
    """The last record against the true record: what was right, wrong, missed, and why a reading was missed."""
    wrong = {e.key: e.cause for e in errors(rec, state, turns, heard or None, listed, final=True)}
    missed = []
    for k, val in state.readings.items():
        if k not in rec.readings:
            lines = [
                t
                for t in turns
                if t.id.isdigit() and any(e.get("equip") == k[0] and e.get("field") == k[1] for e in t.effects)
            ]
            clear = any(said(val, spoken(t, heard).replace("~", "")) for t in lines) if heard else True
            why = "heard, but marked unsure or left out" if clear else "never came through the noise"
            missed.append({"equip": k[0], "label": field_label(k[1])[0], "value": val, "why": why})
    for k, status in state.work.items():
        if rec.work.get(k) != status and k not in wrong:
            why = f"shown as {rec.work[k].replace('_', ' ')}" if k in rec.work else "status not recorded"
            missed.append(
                {"equip": k[0], "label": k[1].replace("_", " "), "value": status.replace("_", " "), "why": why}
            )
    for k, val in state.equipment.items():
        if k not in rec.equipment and not same(val, listed.get(k, "")):
            missed.append({"equip": k[0], "label": k[1], "value": val, "why": "nameplate fact not recorded"})
    hits, total = recall(rec, state, listed)
    return {"hits": hits, "total": total, "wrong": [list(k) + [c] for k, c in wrong.items()], "missed": missed}


def record_view(rec, wrong: dict) -> dict:
    def check(key):
        return wrong.get(key, "ok")

    readings = [{"equip": k[0], "field": k[1], "label": field_label(k[1])[0], "unit": field_label(k[1])[1], "value": v,
                 "evidence": rec.evidence.get(k, []), "check": check(k)} for k, v in rec.readings.items()]  # fmt: skip
    work = [{"equip": k[0], "task": k[1].replace("_", " "), "status": s, "evidence": rec.evidence.get(k, []),
             "check": check(k)} for k, s in rec.work.items()]  # fmt: skip
    unsure = [{"equip": list(eq), "label": field_label(f)[0]} for eq, f in rec.unresolved]
    equipment = [{"equip": k[0], "field": k[1], "value": v} for k, v in rec.equipment.items()]
    return {"readings": readings, "work": work, "unsure": unsure, "equipment": equipment}


def audio_file(visit, t: Turn, kind: str, reply_index: dict) -> str | None:
    if t.speaker == "device":
        return None
    name = f"{visit.id}-{t.id}" if t.id.isdigit() else f"{visit.id}-r{reply_index[t.text]}"
    if kind == "voice" and t.id.isdigit():
        src = WORK.parents[1] / "raw/yash-voice/lines" / f"{name}.wav"
    else:
        src = WORK / "test-Babble-0dB" / ("clean" if kind == "voice" else kind) / f"{name}.wav"
    if not src.exists():
        return None
    dst = AUDIO / kind / f"{name}.wav"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return f"../audio/live/{kind}/{name}.wav"


def build(spec: dict) -> dict:
    visit = load(ROOT / f"live/scenarios/test/{spec['visit']}.json")
    data = json.loads((ROOT / spec["run"] / f"{spec['visit']}.B.json").read_text())
    turns = [Turn(**t) for t in data["turns"]]
    heard = data["heard"] if data["condition"] == "asr" else {}
    listed = visit.listed
    reply_index = {text: k for k, text in enumerate(replies(visit))}
    lines = [{"id": t.id, "speaker": t.speaker, "said": t.text, "heard": heard.get(t.id) or heard.get(REPLY + t.text),
              "audio": audio_file(visit, t, spec["audio"], reply_index)} for t in turns]  # fmt: skip
    steps, rec = [], None
    for s in data["steps"]:
        so_far = heard_until(turns, s["after"])
        rec = normalize(s["record"], visit.equipment_ids)
        wrong = {e.key: e.cause for e in errors(rec, truth_of(so_far), so_far, heard or None, listed)}
        steps.append({"after": s["after"], **record_view(rec, wrong)})
    summary = final_summary(rec, truth_of(turns), turns, heard, listed)
    marks = moments(visit, turns, heard, listed)
    return {**spec, "equipment": visit.equipment, "lines": lines, "steps": steps, "moments": marks, "summary": summary}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    keys = ("visit", "run", "audio", "title", "note")
    visits = [build(dict(zip(keys, spec, strict=True))) for spec in VISITS]
    page = (ROOT / "scripts/live_demo_template.html").read_text()
    (OUT / "index.html").write_text(page.replace("/*DATA*/null", json.dumps(visits)))
    print(f"wrote {OUT / 'index.html'} with {len(visits)} visits, audio in {AUDIO}")


if __name__ == "__main__":
    main()
