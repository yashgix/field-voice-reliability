"""Append-only, hash-chained event log in SQLite, plus content-addressed audio clips.

Records are rebuilt from events and never edited. Database triggers reject UPDATE and DELETE, and each event's hash
covers the previous one, so a change made around the triggers shows up in `verify()`.
"""

import hashlib
import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,
    data TEXT NOT NULL,
    prev TEXT NOT NULL,
    hash TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS events_by_visit ON events (visit_id, seq);
CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
"""
GENESIS = "0" * 64


@dataclass(frozen=True)
class Event:
    seq: int
    visit_id: str
    ts: str
    kind: str
    data: dict


def _digest(prev: str, visit_id: str, ts: str, kind: str, data: str) -> str:
    return hashlib.sha256("|".join((prev, visit_id, ts, kind, data)).encode()).hexdigest()


def _dump(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class EventLog:
    def __init__(self, path: Path | str):
        self._db = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
        self._db.executescript(SCHEMA)
        self._lock = threading.Lock()

    def append(self, visit_id: str, kind: str, data: dict) -> Event:
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                row = self._db.execute("SELECT hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
                prev, ts, body = row[0] if row else GENESIS, datetime.now(UTC).isoformat(), _dump(data)
                cur = self._db.execute(
                    "INSERT INTO events (visit_id, ts, kind, data, prev, hash) VALUES (?, ?, ?, ?, ?, ?)",
                    (visit_id, ts, kind, body, prev, _digest(prev, visit_id, ts, kind, body)),
                )
                self._db.execute("COMMIT")
            except BaseException:
                self._db.execute("ROLLBACK")
                raise
        return Event(cur.lastrowid, visit_id, ts, kind, json.loads(body))

    def events(self, visit_id: str) -> list[Event]:
        rows = self._db.execute(
            "SELECT seq, visit_id, ts, kind, data FROM events WHERE visit_id = ? ORDER BY seq", (visit_id,)
        )
        return [Event(s, v, t, k, json.loads(d)) for s, v, t, k, d in rows]

    def visit_ids(self) -> list[str]:
        rows = self._db.execute("SELECT visit_id FROM events WHERE kind = 'visit_started' ORDER BY seq")
        return [r[0] for r in rows]

    def head(self) -> tuple[int, str]:
        """Event count and last hash. Kept outside the database, they expose events removed from the end."""
        count, last = self._db.execute(
            "SELECT COUNT(*), (SELECT hash FROM events ORDER BY seq DESC LIMIT 1) FROM events"
        ).fetchone()
        return count, last or GENESIS

    def verify(self) -> list[str]:
        """Problems found when recomputing the whole hash chain; empty means intact."""
        problems, expected = [], GENESIS
        for seq, visit_id, ts, kind, data, prev, digest in self._db.execute("SELECT * FROM events ORDER BY seq"):
            if prev != expected:
                problems.append(f"event {seq}: chain broken (previous hash does not match)")
            if digest != _digest(prev, visit_id, ts, kind, data):
                problems.append(f"event {seq}: content changed after it was written")
            expected = digest
        return problems


class ClipStore:
    """Audio clips named by their SHA-256, so an event's clip reference also proves the bytes."""

    def __init__(self, folder: Path):
        self.folder = folder
        folder.mkdir(parents=True, exist_ok=True)

    def save(self, audio: bytes) -> str:
        sha = hashlib.sha256(audio).hexdigest()
        path = self.path(sha)
        if not path.exists():
            path.write_bytes(audio)
        return sha

    def path(self, sha: str) -> Path:
        if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            raise ValueError("not a clip id")
        return self.folder / f"{sha}.wav"

    def intact(self, sha: str) -> bool:
        path = self.path(sha)
        return path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == sha
