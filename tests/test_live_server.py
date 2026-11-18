import json
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest
from test_mvp_server import call

from live.api import SpendCapReached
from live.scenario import load
from live.server import App, make_handler
from live.session import Session
from mvp.events import ClipStore, EventLog

VISIT = load(Path(__file__).resolve().parents[1] / "live/scenarios/test/g04.json")
RECORD = {"readings": [{"equip": "E1", "field": "superheat", "value": "", "status": "unresolved",
                       "options": ["11", "17"], "evidence": ["1"]}],
          "work": [], "equipment": []}  # fmt: skip


class FakeModel:
    """Replies with `RECORD` plus the next scripted question; `gate` holds a call until released."""

    def __init__(self, asks=(), cap_after=None):
        self.asks, self.prompts, self.cap_after, self.record = list(asks), [], cap_after, RECORD
        self.gate = threading.Event()
        self.gate.set()

    def __call__(self, system: str, prompt: str) -> tuple[str, dict]:
        if self.cap_after is not None and len(self.prompts) >= self.cap_after:
            raise SpendCapReached("cap")
        self.prompts.append(prompt)
        self.gate.wait(5)
        ask = {"equip": "E1", "field": "superheat", "question": self.asks.pop(0)} if self.asks else None
        return json.dumps({**self.record, "ask": ask}), {"dollars": 0.001}


def until(check, seconds=5.0):
    end = time.time() + seconds
    while not check():
        assert time.time() < end, "timed out"
        time.sleep(0.01)


@pytest.fixture
def make(tmp_path, asr):
    def build(model):
        return Session(VISIT, EventLog(tmp_path / "events.db"), ClipStore(tmp_path / "clips"), asr, model)

    return build


def test_a_burst_of_lines_is_heard_in_order_and_covered_by_one_update(make, asr):
    model = FakeModel()
    model.gate.clear()
    s = make(model)
    s.add(asr.clip("first line"))
    until(lambda: model.prompts)
    for text in ("second line", "third line", "fourth line"):
        s.add(asr.clip(text))
    model.gate.set()
    until(lambda: all(ln.status == "recorded" for ln in s.lines))
    assert [t.text for t in s.turns] == ["first line", "second line", "third line", "fourth line"]
    assert [u["lines"] for u in s.updates] == [["1"], ["2", "3", "4"]]
    assert "[4] fourth line" in model.prompts[-1] and json.dumps(RECORD) in model.prompts[-1]
    assert asr.calls[0][1].startswith("HVAC service call. Equipment on site: Carrier condenser")


def test_a_question_is_asked_once_and_becomes_a_headset_line(make, asr):
    s = make(FakeModel(asks=["what was the superheat?", "Could you repeat the superheat on E1?"]))
    s.add(asr.clip("superheat is"))
    until(lambda: s.question)
    s.add(asr.clip("eleven"))
    until(lambda: len(s.updates) == 2)
    assert s.question["id"] == "1q" and [t.id for t in s.turns] == ["1", "1q", "2"]
    assert [q["text"] for q in s.state()["questions"]] == ["what was the superheat?"]


def test_the_question_clears_once_its_reading_is_settled(make, asr):
    model = FakeModel(asks=["what was the superheat?"])
    s = make(model)
    s.add(asr.clip("superheat is"))
    until(lambda: s.question)
    model.record = {**RECORD, "readings": [{**RECORD["readings"][0], "status": "final", "value": "11"}]}
    s.add(asr.clip("eleven"))
    until(lambda: len(s.updates) == 2)
    assert s.question is None and [q["id"] for q in s.state()["questions"]] == ["1q"]


def test_a_question_is_dropped_when_the_technician_keeps_talking(make, asr):
    model = FakeModel(asks=["which unit?"])
    model.gate.clear()
    s = make(model)
    s.add(asr.clip("suction is one eighteen"))
    until(lambda: model.prompts)
    s.add(asr.clip("on the rear unit"))
    model.gate.set()
    until(lambda: len(s.updates) == 2)
    assert s.question is None
    assert "question_dropped" in [e.kind for e in s.log.events(s.id)]


def test_silence_adds_no_line_to_the_transcript(make, asr):
    s = make(FakeModel())
    s.add(asr.clip(""))
    until(lambda: s.lines[0].status == "silent")
    assert s.turns == [] and s.updates == []


def test_the_spend_cap_stops_model_calls_but_not_listening(make, asr):
    s = make(FakeModel(cap_after=1))
    s.add(asr.clip("one"))
    until(lambda: s.updates)
    s.add(asr.clip("two"))
    until(lambda: s.capped)
    s.add(asr.clip("three"))
    until(lambda: s.lines[2].heard == "three")
    assert len(s.updates) == 1 and s.error == "cap"
    assert s.log.verify() == []


@pytest.fixture
def server(tmp_path, asr):
    app = App(tmp_path, VISIT, asr, FakeModel(), "secret-token")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(app))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}", app
    httpd.shutdown()


def test_http_flow_needs_the_token_and_serves_only_a_sessions_own_clips(server, asr):
    base, app = server
    assert call(base, "POST", "/api/sessions", {}, token="wrong")[0] == 401
    assert all(call(base, "GET", f"/{name}")[0] == 200 for name in ("", "worklet.js", "listener.js"))
    assert call(base, "GET", "/server.py")[0] == 404
    one = json.loads(call(base, "POST", "/api/sessions", {})[1])["session"]
    other = json.loads(call(base, "POST", "/api/sessions", {})[1])["session"]
    assert call(base, "POST", f"/api/sessions/{one}/audio", b"not audio", "audio/wav")[0] == 415
    status, body = call(base, "POST", f"/api/sessions/{one}/audio", asr.clip("superheat eleven"), "audio/wav")
    assert status == 202 and json.loads(body) == {"line": "1"}
    until(lambda: app.sessions[one].lines[0].status == "recorded")
    state = json.loads(call(base, "GET", f"/api/sessions/{one}")[1])
    clip = state["lines"][0]["clip"]
    assert state["record"] == RECORD
    assert call(base, "GET", f"/api/sessions/{one}/clips/{clip}")[1] == asr.clip("superheat eleven")
    assert call(base, "GET", f"/api/sessions/{other}/clips/{clip}")[0] == 404
    status, body = call(base, "POST", f"/api/sessions/{one}/full", asr.clip("the whole visit"), "audio/wav")
    assert status == 202 and app.clips.intact(json.loads(body)["clip"])
    assert [e.kind for e in app.log.events(one)][-1] == "session_audio"


def test_a_question_about_a_settled_reading_is_dropped(make, asr):
    model = FakeModel(asks=["what was the superheat?"])
    model.record = {**RECORD, "readings": [{**RECORD["readings"][0], "status": "final", "value": "11"}]}
    s = make(model)
    s.add(asr.clip("superheat eleven"))
    until(lambda: s.updates)
    until(lambda: "question_dropped" in [e.kind for e in s.log.events(s.id)])
    assert s.question is None
