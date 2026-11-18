"""One hands-free visit: spoken lines are queued, heard by Whisper with the job prompt, and kept as a job record by
design B (the record so far plus every line so far) through the API.

Lines are heard one at a time in arrival order, and the model runs only once no line waits, so a burst of speech is
covered by one update and no line is dropped. A question is put to the technician only if nothing new was said while
the model was deciding, and the same question is never asked twice.
"""

import queue
import secrets
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass

from fvr.asr import Decode
from live.api import SpendCapReached
from live.arms import SYSTEM, Caller, parse_record, record_prompt
from live.render import heard_text, job_prompt
from live.scenario import Turn, Visit
from mvp.events import ClipStore, EventLog

Transcriber = Callable[[str, str | None], Decode]
NOTE = (
    'Write the full record as it stands now. A rated or expected value ("it should be 35") is not a reading. An '
    'installed replacement ("new capacitor is in") is done. Speech recognition writes a decimal with a space ("34 .7" '
    'is 34.7) and sometimes writes "one twenty" the same way ("1 .20"). Read such a number as the value that makes '
    "sense for the reading, and keep it unresolved and ask only if both make sense."
)


@dataclass
class Line:
    id: str
    clip: str
    received: float
    heard: str | None = None  # Whisper's words, unsure ones marked with ~
    heard_at: float | None = None
    recorded_at: float | None = None  # when a record update first covered this line

    @property
    def status(self) -> str:
        if self.recorded_at:
            return "recorded"
        if self.heard == "":
            return "silent"
        return "updating" if self.heard_at else "queued"


def _ids(equip) -> set[str]:
    return {str(e) for e in (equip if isinstance(equip, list) else [equip]) if e}


def topic(ask: dict) -> str:
    """What a question is about: its field on its equipment, so a reworded question counts as a repeat."""
    if not ask.get("field"):
        return str(ask["question"]).strip().lower()
    return f"{ask['field']}@{','.join(sorted(_ids(ask.get('equip'))))}"


def about_open_entry(record: dict | None, ask: dict) -> bool:
    """The instructions allow a question only about a reading the record leaves unsettled, so hold the model to it."""
    asked = _ids(ask.get("equip"))
    for r in (record or {}).get("readings") or []:
        equips = _ids(r.get("equip"))
        unsettled = r.get("status") == "unresolved" or len(equips) > 1
        if unsettled and r.get("field") == ask.get("field") and (not asked or asked & equips):
            return True
    return False


class Session:
    def __init__(self, visit: Visit, log: EventLog, clips: ClipStore, transcribe: Transcriber, ask_model: Caller):
        self.id, self.visit, self.log, self.clips = secrets.token_hex(6), visit, log, clips
        self.transcribe, self.ask_model, self.prompt = transcribe, ask_model, job_prompt(visit, with_fields=False)
        self.lines: list[Line] = []
        self.turns: list[Turn] = []
        self.record: dict | None = None
        self.question: dict | None = None
        self.asked: set[str] = set()  # topics already asked about
        self.updates: list[dict] = []
        self.error: str | None = None  # the latest failure, shown on the page
        self.capped = False
        self.inbox: queue.Queue[Line] = queue.Queue()
        self.lock = threading.Lock()
        log.append(self.id, "visit_started", {"visit": visit.id, "equipment": visit.equipment})
        threading.Thread(target=self._work, daemon=True).start()

    def add(self, audio: bytes) -> str:
        """Save a spoken line's audio and queue it. Returns the line id at once."""
        sha = self.clips.save(audio)
        with self.lock:
            line = Line(str(len(self.lines) + 1), sha, time.time())
            self.lines.append(line)
        self.log.append(self.id, "line_received", {"line": line.id, "clip": sha})
        self.inbox.put(line)
        return line.id

    def keep_whole(self, audio: bytes) -> str:
        """The whole session as the microphone heard it, kept to check the page's voice detector against."""
        sha = self.clips.save(audio)
        self.log.append(self.id, "session_audio", {"clip": sha})
        return sha

    def _work(self) -> None:
        while True:
            line = self.inbox.get()
            try:
                self._hear(line)
                if self.inbox.empty() and not self.capped:
                    self._update()
            except SpendCapReached as e:
                self.capped, self.error = True, str(e)
            except Exception as e:  # one bad line or call must not stop the visit
                self.error = f"{type(e).__name__}: {e}"
                self.log.append(self.id, "error", {"line": line.id, "error": self.error})

    def _hear(self, line: Line) -> None:
        d = self.transcribe(str(self.clips.path(line.clip)), self.prompt)
        text = heard_text(d.words)
        with self.lock:
            line.heard, line.heard_at = text, time.time()
            if text:
                self.turns.append(Turn(line.id, "tech", text))
        self.log.append(self.id, "line_heard", {"line": line.id, "text": d.text, "heard": text})

    def _update(self) -> None:
        with self.lock:
            turns, previous = list(self.turns), self.record
            covered = [ln for ln in self.lines if ln.heard and not ln.recorded_at]
        if not covered:
            return
        raw, meta = self.ask_model(SYSTEM, record_prompt(self.visit, turns, {}, NOTE, previous))
        record, now = parse_record(raw), time.time()
        ask = (record or {}).pop("ask", None)
        with self.lock:
            for ln in covered:
                ln.recorded_at = now
            if record is not None:
                self.record = record
                if not self.capped:
                    self.error = None  # an earlier failure no longer applies
                if self.question and not about_open_entry(record, self.question):
                    self.question = None  # the reading it asked about is settled
            self.updates.append({**meta, "lines": [ln.id for ln in covered], "parsed": record is not None})
        self.log.append(self.id, "record_updated", {"raw": raw, "record": record, "meta": meta,
                                                    "lines": [ln.id for ln in covered]})  # fmt: skip
        self._maybe_ask(ask, record, turns[-1].id)

    def _maybe_ask(self, ask: dict | None, record: dict | None, after: str) -> None:
        text = str((ask or {}).get("question") or "").strip()
        key = topic(ask) if text else ""
        if not text or key in self.asked:
            return
        if not about_open_entry(record, ask):
            self.log.append(self.id, "question_dropped", {"question": text, "reason": "nothing unsettled"})
            return
        if not self.inbox.empty():  # the technician kept talking, so the question may already be stale
            self.log.append(self.id, "question_dropped", {"question": text, "reason": "new speech"})
            return
        with self.lock:
            self.asked.add(key)
            self.question = {"id": f"{after}q", "text": text, "equip": ask.get("equip"), "field": ask.get("field")}
            self.turns.append(Turn(f"{after}q", "device", text))
        self.log.append(self.id, "question_asked", self.question)

    def state(self) -> dict:
        with self.lock:
            lines = [{**asdict(ln), "status": ln.status} for ln in self.lines]
            questions = [{"id": t.id, "text": t.text} for t in self.turns if t.speaker == "device"]
            return {"session": self.id, "visit": self.visit.id, "equipment": self.visit.equipment,
                    "record": self.record, "question": self.question, "questions": questions, "lines": lines,
                    "waiting": self.inbox.qsize(), "updates": self.updates, "error": self.error}  # fmt: skip

    def owns(self, clip: str) -> bool:
        with self.lock:
            return any(ln.clip == clip for ln in self.lines)
