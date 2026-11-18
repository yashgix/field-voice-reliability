"""Visit actions: each one appends events, then the visit is rebuilt from the log and the next prompt returned."""

import io
import subprocess
import threading
import uuid
import wave
from collections.abc import Callable
from pathlib import Path

import numpy as np

from fvr.asr import Decode
from fvr.readings import Settings
from mvp.events import ClipStore, EventLog
from mvp.visit import (
    MAX_FAILED_ANSWERS,
    Ask,
    Fill,
    Visit,
    fill_status,
    job_prompt,
    judge_answer,
    judge_reading,
    next_check,
    prompt,
    readback_items,
    replay,
    seeded_errors,
    typed_reading,
)

Transcriber = Callable[[str, str | None], Decode]
MIN_SECONDS, MAX_SECONDS, SILENCE_PEAK = 0.4, 30.0, 0.01


class ActionError(ValueError):
    """A request that does not fit the visit's current state."""


def audio_problem(audio: bytes) -> str | None:
    """Why a clip cannot be recognised, or None. Checked before any recognition."""
    try:
        with wave.open(io.BytesIO(audio)) as w:
            if w.getsampwidth() != 2:
                return "unsupported sample format"
            frames, rate, channels = w.readframes(w.getnframes()), w.getframerate(), w.getnchannels()
    except (wave.Error, EOFError):
        return "not a WAV file"
    samples = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768
    seconds = len(samples) / max(1, rate * channels)
    if seconds < MIN_SECONDS:
        return "too short"
    if seconds > MAX_SECONDS:
        return "too long"
    if np.abs(samples).max(initial=0) < SILENCE_PEAK:
        return "silent"
    return None


class Engine:
    def __init__(self, log: EventLog, clips: ClipStore, transcribe: Transcriber, settings: Settings, versions: dict):
        self.log, self.clips, self.transcribe, self.settings, self.versions = log, clips, transcribe, settings, versions
        self._lock = threading.Lock()  # one action at a time: the model and the visit state are shared

    def visit(self, visit_id: str) -> Visit:
        events = self.log.events(visit_id)
        if not events:
            raise ActionError("unknown visit")
        return replay(events)

    def start(self, job: dict, evaluation: dict | None = None) -> str:
        visit_id = uuid.uuid4().hex[:12]
        self.log.append(visit_id, "visit_started", {"job": job, "versions": self.versions, "eval": evaluation})
        return visit_id

    def audio(self, visit_id: str, utt_id: str, slot_key: str, audio: bytes) -> dict:
        with self._lock:
            v = self.visit(visit_id)
            if utt_id in v.utt_ids:
                return prompt(v)  # a retried upload of a clip already handled
            pending = v.pending_slot()
            if pending and slot_key not in ("", pending.key):
                raise ActionError(f"answer the open question about {pending.label} first")
            slot = pending or v.slots.get(slot_key)
            if slot is None or v.stage in ("readback", "closed") or (slot.status != "open" and not slot.pending):
                raise ActionError("no reading is expected for this slot now")
            answering = slot.pending is not None
            yes_no = answering and slot.pending.kind == "yesno"
            sha, problem = self.clips.save(audio), audio_problem(audio)
            decode = (
                None if problem else self.transcribe(str(self.clips.path(sha)), None if yes_no else job_prompt(v.job))
            )
            text, words = (decode.text, decode.words) if decode else ("", [])
            self.log.append(
                visit_id,
                "utterance",
                {
                    "utt_id": utt_id,
                    "slot": slot.key,
                    "purpose": "answer" if answering else "reading",
                    "clip": sha,
                    "problem": problem,
                    "transcript": text,
                    "words": words,
                    "seconds": round(decode.seconds, 3) if decode else 0,
                },
            )
            outcome = (
                judge_answer(text, words, slot, self.settings)
                if answering
                else judge_reading(text, words, slot, self.settings)
            )
            self._apply(visit_id, self.visit(visit_id).slots[slot.key], outcome, answering, by="technician_voice")
            return self._advance(visit_id)

    def _apply(self, visit_id: str, slot, outcome: Fill | Ask, answering: bool, by: str) -> None:
        if isinstance(outcome, Fill):
            r = outcome.reading
            self.log.append(
                visit_id,
                "value_set",
                {
                    "slot": slot.key,
                    "value": r.value,
                    "unit": r.unit,
                    "status": fill_status(slot, r, answering),
                    "by": by if answering or slot.previous is not None else "checker",
                },
            )
            return
        failed = (slot.pending.failed if slot.pending else 0) + int(answering and outcome.failed)
        if failed >= MAX_FAILED_ANSWERS:
            self.log.append(
                visit_id, "unconfirmed", {"slot": slot.key, "reason": "clarification failed", "clips": slot.clips}
            )
            return
        self.log.append(
            visit_id,
            "question",
            {
                "slot": slot.key,
                "kind": outcome.kind,
                "text": outcome.text,
                "failed": failed,
                "proposed": {"value": outcome.proposed.value, "unit": outcome.proposed.unit}
                if outcome.proposed
                else None,
            },
        )

    def tap(self, visit_id: str, action: str, slot_key: str = "", value: str = "", unit: str = "") -> dict:
        with self._lock:
            v = self.visit(visit_id)
            if v.stage == "closed":
                raise ActionError("this visit is saved and closed")
            slot = v.slots.get(slot_key) or v.pending_slot()
            if action in ("yes", "no"):
                self._tap_yes_no(visit_id, v, action)
            elif action == "typed":
                self._typed(visit_id, v, slot, value.strip(), unit)
            elif action == "skip":
                self._skip(visit_id, slot)
            elif action == "finish" and v.stage == "capture" and v.open_slots() and not v.pending_slot():
                self.log.append(visit_id, "missing_shown", {"slots": [s.key for s in v.open_slots()]})
            elif action == "skip_missing" and v.stage == "missing":
                for s in v.open_slots():
                    self.log.append(visit_id, "skipped", {"slot": s.key, "reason": "skipped at end of visit"})
            elif action in ("confirm", "fix", "played") and v.stage == "readback":
                self._check(visit_id, v, action, slot_key)
            elif action == "interrupted" and slot_key in v.slots:
                self.log.append(visit_id, "capture_interrupted", {"slot": slot_key, "reason": value[:80]})
            else:
                raise ActionError(f"'{action}' is not possible now")
            return self._advance(visit_id)

    def _check(self, visit_id: str, v: Visit, action: str, slot_key: str) -> None:
        """Read-back, one value at a time: only the value on screen can be confirmed or corrected, so a stale or
        repeated tap never approves the next one."""
        item = next_check(v)
        if slot_key != item["slot"]:
            raise ActionError(f"check {item['label']} first")
        if action == "played":
            self.log.append(visit_id, "audio_played", {"slot": slot_key})
        elif action == "confirm":
            self.log.append(visit_id, "value_checked", {"slot": slot_key, "shown": item})
        else:
            slot = v.slots[slot_key]
            self.log.append(
                visit_id,
                "reopened",
                {
                    "slot": slot_key,
                    "from": "readback",
                    "shown": item,
                    "previous": {"value": slot.value, "unit": slot.unit},
                },
            )

    def _tap_yes_no(self, visit_id: str, v: Visit, action: str) -> None:
        slot = v.pending_slot()
        if not slot or slot.pending.kind != "yesno":
            raise ActionError("no yes or no question is open")
        outcome = judge_answer(action, [], slot, self.settings)  # a tap means exactly what the spoken word would
        self._apply(visit_id, slot, outcome, answering=True, by="technician_tap")

    def _typed(self, visit_id: str, v: Visit, slot, value: str, unit: str) -> None:
        if not slot or v.stage == "closed" or not (slot.pending or slot.status == "open"):
            raise ActionError("open the reading first")
        r = typed_reading(slot, value, unit)
        if r is None:
            raise ActionError("type a number and pick the unit")
        status = fill_status(slot, r, answered=True)
        self.log.append(
            visit_id,
            "value_set",
            {"slot": slot.key, "value": r.value, "unit": r.unit, "status": status, "by": "technician_typed"},
        )

    def _skip(self, visit_id: str, slot) -> None:
        if not slot or not (slot.pending or slot.status == "open"):
            raise ActionError("nothing to skip")
        if slot.clips:
            self.log.append(
                visit_id, "unconfirmed", {"slot": slot.key, "reason": "technician skipped", "clips": slot.clips}
            )
        else:
            self.log.append(visit_id, "skipped", {"slot": slot.key, "reason": "technician skipped"})

    def _advance(self, visit_id: str) -> dict:
        """Start the read-back once every reading is resolved; save the visit once every value is checked."""
        v = self.visit(visit_id)
        if v.stage in ("capture", "missing") and not v.open_slots() and not v.pending_slot():
            seeded = seeded_errors(v)
            self.log.append(visit_id, "readback_shown", {"items": readback_items(v, seeded), "seeded": seeded})
            v = self.visit(visit_id)
        if v.stage == "readback" and next_check(v) is None:
            self.log.append(visit_id, "visit_closed", {})
            v = self.visit(visit_id)
        return prompt(v)


def versions(root: Path, model: str) -> dict:
    """Code commit (marked dirty if the working tree differs) and model, stored with every visit."""
    git = ["git", "-C", str(root)]
    commit = subprocess.run([*git, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run([*git, "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True)
    return {"code": commit + ("+dirty" if dirty.stdout.strip() else ""), "model": model}
