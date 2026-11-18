import sqlite3

import pytest
from conftest import wav

from mvp.engine import audio_problem
from mvp.events import ClipStore, EventLog


def test_events_cannot_be_updated_or_deleted(tmp_path):
    log = EventLog(tmp_path / "e.db")
    log.append("v1", "visit_started", {"job": {}})
    db = sqlite3.connect(tmp_path / "e.db")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        db.execute("UPDATE events SET data = '{}'")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        db.execute("DELETE FROM events")


def test_an_edit_made_around_the_triggers_is_detected(tmp_path):
    log = EventLog(tmp_path / "e.db")
    for value in ("118", "342", "12"):
        log.append("v1", "value_set", {"value": value})
    assert log.verify() == []
    db = sqlite3.connect(tmp_path / "e.db")
    db.execute("DROP TRIGGER events_no_update")
    db.execute("""UPDATE events SET data = '{"value":"128"}' WHERE seq = 1""")
    db.commit()
    assert log.verify() == ["event 1: content changed after it was written"]
    db.execute("DROP TRIGGER events_no_delete")
    db.execute("DELETE FROM events WHERE seq = 2")
    db.commit()
    assert "event 3: chain broken (previous hash does not match)" in log.verify()


def test_clips_are_named_by_hash_and_checked(tmp_path):
    clips = ClipStore(tmp_path / "clips")
    sha = clips.save(wav())
    assert clips.intact(sha)
    clips.path(sha).write_bytes(wav(amplitude=0.5))
    assert not clips.intact(sha)
    with pytest.raises(ValueError):
        clips.path("../../etc/passwd")


def test_audio_problems_are_found_before_recognition():
    assert audio_problem(b"not audio") == "not a WAV file"
    assert audio_problem(wav(seconds=0.2)) == "too short"
    assert audio_problem(wav(seconds=31)) == "too long"
    assert audio_problem(wav(amplitude=0.0)) == "silent"
    assert audio_problem(wav(rate=48000)) is None
