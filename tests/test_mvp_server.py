import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest
from conftest import JOBS, wav

from mvp.server import App, make_handler

SCHEDULE = {"demo-electrical": [{"slot": "ground", "shown": "52", "type": "swapped"}]}


@pytest.fixture
def server(tmp_path, asr):
    app = App(tmp_path, JOBS, asr, "secret-token", None)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(app))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}", asr
    httpd.shutdown()


def call(base, method, path, body=None, kind="application/json", token="secret-token"):
    data = json.dumps(body).encode() if kind == "application/json" and body is not None else body
    req = urllib.request.Request(
        base + path, data=data, method=method, headers={"X-Token": token, "Content-Type": kind}
    )
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, res.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_api_needs_the_token(server):
    base, _ = server
    assert call(base, "GET", "/api/jobs", token="wrong")[0] == 401
    assert call(base, "GET", "/")[0] == 200  # the page itself holds no data


def test_static_files_cannot_escape_the_folder(server):
    base, _ = server
    for path in ("/../server.py", "/%2e%2e/server.py", "/static/../../fvr/asr.py", "/events.db"):
        assert call(base, "GET", path)[0] == 404, path


def test_full_visit_over_http(server):
    base, asr = server
    status, body = call(base, "POST", "/api/visits", {"job": "demo-electrical"})
    state = json.loads(body)
    assert status == 201 and state["prompt"]["slot"] == "line_voltage"
    vid = state["visit_id"]
    for i, (slot, text) in enumerate([("line_voltage", "Line voltage is 240 volts."), ("l1_amps", "60 amps."),
                                      ("l2_amps", "58 amps."), ("ground", "25 ohms.")]):  # fmt: skip
        status, body = call(
            base, "POST", f"/api/visits/{vid}/audio?slot={slot}&utt={i:08x}-0000", asr.clip(text), "audio/wav"
        )
        assert status == 200, body
    state = json.loads(body)
    assert state["prompt"]["expect"] == "readback" and state["heard"] == ""  # cleared at read-back
    for slot in ("line_voltage", "l1_amps", "l2_amps", "ground"):
        state = json.loads(call(base, "POST", f"/api/visits/{vid}/tap", {"action": "confirm", "slot": slot})[1])
    assert state["stage"] == "closed"
    record = json.loads(call(base, "GET", f"/api/visits/{vid}/record")[1])
    assert [r["value"] for r in record["readings"]] == ["240", "60", "58", "25"]
    assert record["audit"] == {
        "events": 15,
        "chain_problems": [],
        "clips_missing_or_changed": [],
        "untraceable_values": [],
    }
    clip = record["readings"][0]["evidence"][0]["clip"]
    assert call(base, "GET", f"/api/visits/{vid}/clips/{clip}")[1].startswith(b"RIFF")
    assert call(base, "GET", f"/api/visits/{vid}/clips/{'0' * 64}")[0] == 404


def test_a_planted_value_is_never_revealed_before_the_visit_is_saved(tmp_path, asr):
    app = App(tmp_path, JOBS, asr, "t", SCHEDULE)
    vid = app.engine.start(app.jobs["demo-electrical"], {"schedule": SCHEDULE["demo-electrical"]})
    said = {"line_voltage": "240 volts.", "l1_amps": "60 amps.", "l2_amps": "58 amps.", "ground": "25 ohms."}
    for slot, text in said.items():
        app.engine.audio(vid, f"{slot:0<8}", slot, asr.clip(text))
    seed = app.engine.visit(vid).readback["seeded"][0]
    state = app.state(vid)
    assert state["heard"] == "" and {s["key"]: s["value"] for s in state["slots"]}[seed["slot"]] == seed["shown"]
    other = next(k for k in said if k != seed["slot"])
    while (current := app.state(vid)["prompt"]["item"]["slot"]) != other:
        app.engine.tap(vid, "confirm", current)
    app.engine.tap(vid, "fix", other)  # correcting another value shows neither the real value nor its transcript
    state = app.state(vid)
    assert state["heard"] == "" and [s["value"] for s in state["slots"]] == [None] * 4


def test_an_evaluation_run_shows_no_value_while_recording(tmp_path, asr):
    """Values appear only at the read-back, so a planted value never shows as a change from one seen before."""
    app = App(tmp_path, JOBS, asr, "t", {})  # practice: evaluation mode with nothing planted
    vid = app.engine.start(app.jobs["demo-electrical"], {"schedule": []})
    app.engine.audio(vid, "line0000", "line_voltage", asr.clip("240 volts."))
    assert [s["value"] for s in app.state(vid)["slots"]] == [None] * 4
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(app))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    assert call(f"http://127.0.0.1:{httpd.server_port}", "GET", f"/api/visits/{vid}/record", token="t")[0] == 403
    httpd.shutdown()


def test_after_saving_an_evaluation_visit_no_value_or_record_is_returned(tmp_path, asr):
    app = App(tmp_path, JOBS, asr, "t", SCHEDULE)
    vid = app.engine.start(app.jobs["demo-electrical"], {"schedule": SCHEDULE["demo-electrical"]})
    said = {"line_voltage": "240 volts.", "l1_amps": "60 amps.", "l2_amps": "58 amps.", "ground": "25 ohms."}
    for slot, text in said.items():
        app.engine.audio(vid, f"{slot:0<8}", slot, asr.clip(text))
    while app.engine.visit(vid).stage == "readback":
        app.engine.tap(vid, "confirm", app.state(vid)["prompt"]["item"]["slot"])
    assert [s["value"] for s in app.state(vid)["slots"]] == [None] * 4  # neither the planted nor the real value
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(app))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    assert call(f"http://127.0.0.1:{httpd.server_port}", "GET", f"/api/visits/{vid}/record", token="t")[0] == 403
    httpd.shutdown()


def test_an_evaluation_visit_gets_its_jobs_schedule_and_a_bad_schedule_is_refused(tmp_path, asr):
    app = App(tmp_path, JOBS, asr, "t", SCHEDULE)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(app))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_port}"
    for job, plan in (("demo-electrical", SCHEDULE["demo-electrical"]), ("demo-hvac", [])):
        vid = json.loads(call(base, "POST", "/api/visits", {"job": job}, token="t")[1])["visit_id"]
        assert app.engine.visit(vid).eval == {"schedule": plan}
    httpd.shutdown()
    with pytest.raises(ValueError):
        App(tmp_path, JOBS, asr, "t", {"demo-hvac": [{"slot": "ground", "shown": "1", "type": "x"}]})
    with pytest.raises(KeyError):
        App(tmp_path, JOBS, asr, "t", {"no-such-job": []})


def test_bad_uploads_are_refused(server):
    base, _ = server
    vid = json.loads(call(base, "POST", "/api/visits", {"job": "demo-hvac"})[1])["visit_id"]
    audio = f"/api/visits/{vid}/audio?slot=suction&utt=00000001-0000"
    assert call(base, "POST", audio, b"\x00" * 100, "audio/webm")[0] == 415
    assert call(base, "POST", f"/api/visits/{vid}/audio?slot=suction&utt=../x", wav(), "audio/wav")[0] == 400
    assert call(base, "POST", f"/api/visits/{vid}/tap", {"action": "confirm"})[0] == 409
    assert call(base, "POST", "/api/visits", {"job": "no-such-job"})[0] == 400


def test_upload_size_and_length_header_are_checked(server):
    import http.client

    base, _ = server
    vid = json.loads(call(base, "POST", "/api/visits", {"job": "demo-hvac"})[1])["visit_id"]
    host = base.removeprefix("http://")
    for length, expected in (("-1", 400), ("abc", 400), (str(13 * 1024 * 1024), 413)):
        conn = http.client.HTTPConnection(host, timeout=5)
        conn.putrequest("POST", f"/api/visits/{vid}/audio?slot=suction&utt=00000001-0000")
        for name, value in (("X-Token", "secret-token"), ("Content-Type", "audio/wav"), ("Content-Length", length)):
            conn.putheader(name, value)
        conn.endheaders()
        assert conn.getresponse().status == expected, length
        conn.close()
