"""Local web server for the visit app (standard library only).

Binds to localhost by default. `--lan` (for the iPhone) also needs `--https`. Every API call needs the per-run token
printed at start, which the page reads from the URL fragment, so the fragment never reaches any log.
"""

import argparse
import json
import re
import secrets
import socket
import ssl
import threading
import wave
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fvr.paths import DATA, ROOT
from fvr.readings import Settings
from mvp.engine import ActionError, Engine, Transcriber, versions
from mvp.events import ClipStore, EventLog
from mvp.record import build_record
from mvp.visit import prompt

STATIC = Path(__file__).parent / "static"
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css"}
MAX_BODY = 12 * 1024 * 1024
VISIT = re.compile(r"^/api/visits/([0-9a-f]{12})(/[a-z]+)?(/[0-9a-f]{64})?$")


class App:
    def __init__(self, data: Path, jobs: Path, transcribe: Transcriber, token: str, schedule: dict | None):
        data.mkdir(parents=True, exist_ok=True)
        self.log = EventLog(data / "events.db")
        self.clips = ClipStore(data / "clips")
        self.jobs = {j["id"]: j for j in (json.loads(p.read_text()) for p in sorted(jobs.glob("*.json")))}
        settings = Settings(**json.loads((ROOT / "results/readings_settings.json").read_text()))
        self.engine = Engine(self.log, self.clips, transcribe, settings, versions(ROOT, "whisper-large-v3-turbo"))
        self.token = token
        self.evaluation = schedule  # evaluation mode: job id -> wrong values to show at read-back
        for job_id, plan in (schedule or {}).items():
            keys = {c["key"] for c in self.jobs[job_id]["checklist"]}
            if any(p["slot"] not in keys for p in plan):
                raise ValueError(f"schedule names a reading that job {job_id} does not have")

    def state(self, visit_id: str) -> dict:
        v = self.engine.visit(visit_id)
        # in an evaluation run values are returned only during the read-back, with planted values in place, so a
        # planted value never shows as a change from a value seen earlier and is never revealed after it
        planted = {x["slot"]: x["shown"] for x in v.readback["seeded"]} if v.readback else {}
        hidden = self.evaluation is not None and v.stage != "readback"
        slots = [
            {
                "key": s.key,
                "label": s.label,
                "units": s.units,
                "status": s.status,
                "value": None if hidden else planted.get(s.key, s.value),
                "unit": s.unit,
            }
            for s in v.slots.values()
        ]
        job = {"id": v.job["id"], "title": v.job["title"]}
        heard = self._heard(visit_id)
        return {"visit_id": visit_id, "job": job, "stage": v.stage, "prompt": prompt(v), "slots": slots, "heard": heard}

    def _heard(self, visit_id: str) -> str:
        """The last transcript, cleared when the read-back starts or a value is reopened, so it only ever shows what
        was just said for the value being recorded and never a planted value's real reading."""
        heard = ""
        for e in self.log.events(visit_id):
            if e.kind == "utterance":
                heard = e.data["transcript"]
            elif e.kind in ("readback_shown", "reopened"):
                heard = ""
        return heard


class BaseHandler(BaseHTTPRequestHandler):
    """Shared by the capture app and live mode: timeouts, quiet logs, safe headers, the token check, body limits."""

    token = ""
    max_body = MAX_BODY
    timeout = 30  # a stalled client cannot hold a thread for long

    def setup(self) -> None:
        self.request.settimeout(self.timeout)
        if isinstance(self.request, ssl.SSLSocket):
            self.request.do_handshake()  # here, not in the accept loop, so one idle client cannot block others
        super().setup()

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.command} {urlparse(self.path).path} {args[1] if len(args) > 1 else ''}", flush=True)

    def _send(self, status: int, body: bytes, kind: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; media-src 'self' blob:")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data: dict, status: int = HTTPStatus.OK) -> None:
        self._send(status, json.dumps(data).encode(), "application/json")

    def _authorised(self) -> bool:
        if secrets.compare_digest(self.headers.get("X-Token", ""), self.token):
            return True
        self._json({"error": "missing or wrong token"}, HTTPStatus.UNAUTHORIZED)
        return False

    def _body(self) -> bytes | None:
        header = self.headers.get("Content-Length") or "0"
        if not header.isdigit():
            self._json({"error": "bad Content-Length"}, HTTPStatus.BAD_REQUEST)
            return None
        if int(header) > self.max_body:
            self._json({"error": "upload too large"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return None
        return self.rfile.read(int(header))


def make_handler(app: App) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHandler):
        token = app.token

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if not path.startswith("/api/"):
                return self._static(path)
            if not self._authorised():
                return None
            try:
                return self._get_api(path)
            except ActionError as e:
                return self._json({"error": str(e)}, HTTPStatus.NOT_FOUND)

        def _static(self, path: str) -> None:
            name = "index.html" if path == "/" else path.lstrip("/")
            file = (STATIC / name).resolve()
            if file.parent != STATIC.resolve() or not file.is_file() or file.suffix not in TYPES:
                return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return self._send(HTTPStatus.OK, file.read_bytes(), TYPES[file.suffix])

        def _get_api(self, path: str) -> None:
            if path == "/api/jobs":
                jobs = [{"id": j["id"], "title": j["title"]} for j in app.jobs.values()]
                return self._json({"jobs": jobs, "evaluation": app.evaluation is not None})
            if path == "/api/audit":
                return self._json({"chain_problems": app.log.verify(), "visits": app.log.visit_ids()})
            m = VISIT.match(path)
            if not m:
                return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            visit_id, action, clip = m.group(1), m.group(2), (m.group(3) or "").lstrip("/")
            if action is None:
                return self._json(app.state(visit_id))
            if action == "/record" and app.evaluation is not None:
                return self._json({"error": "the record is not shown during an evaluation run"}, HTTPStatus.FORBIDDEN)
            if action == "/record":
                return self._json(build_record(app.log, app.clips, visit_id))
            if action == "/clips" and clip in {c for s in app.engine.visit(visit_id).slots.values() for c in s.clips}:
                return self._send(HTTPStatus.OK, app.clips.path(clip).read_bytes(), "audio/wav")
            return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            url = urlparse(self.path)
            if not self._authorised():
                return None
            body = self._body()
            if body is None:
                return None
            try:
                return self._post_api(url.path, parse_qs(url.query), body)
            except ActionError as e:
                return self._json({"error": str(e)}, HTTPStatus.CONFLICT)
            except (ValueError, KeyError) as e:
                return self._json({"error": f"bad request: {e}"}, HTTPStatus.BAD_REQUEST)

        def _post_api(self, path: str, query: dict, body: bytes) -> None:
            if path == "/api/visits":
                job = app.jobs[json.loads(body or b"{}")["job"]]
                plan = None if app.evaluation is None else {"schedule": app.evaluation.get(job["id"], [])}
                return self._json(app.state(app.engine.start(job, plan)), HTTPStatus.CREATED)
            m = VISIT.match(path)
            if not m or m.group(3):
                return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            visit_id, action = m.group(1), m.group(2)
            if action == "/audio":
                if self.headers.get("Content-Type", "") != "audio/wav":
                    return self._json({"error": "send 16-bit PCM WAV"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
                utt, slot = query["utt"][0], query.get("slot", [""])[0]
                if not re.fullmatch(r"[0-9a-f-]{8,40}", utt):
                    raise ValueError("bad utterance id")
                app.engine.audio(visit_id, utt, slot, body)
                return self._json(app.state(visit_id))
            if action == "/tap":
                d = json.loads(body)
                app.engine.tap(visit_id, d["action"], d.get("slot", ""), str(d.get("value", "")), d.get("unit", ""))
                return self._json(app.state(visit_id))
            return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    return Handler


def silent_wav(path: Path) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(16000), w.writeframes(b"\0\0" * 16000)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--lan", action="store_true", help="listen on the local network (needs --https)")
    ap.add_argument("--https", action="store_true", help="use the certificate made by scripts/mvp_cert.sh")
    ap.add_argument("--data", type=Path, default=DATA / "mvp")
    ap.add_argument("--jobs", type=Path, default=Path(__file__).parent / "jobs")
    ap.add_argument("--evaluation-schedule", type=Path, help="evaluation mode: wrong values to show")
    args = ap.parse_args()
    if args.lan and not args.https:
        ap.error("--lan needs --https: iPhone Safari only allows the microphone on a secure page")
    from fvr.asr import load_engine, transcribe

    load_engine()  # on the main thread, before any worker decodes

    schedule = json.loads(args.evaluation_schedule.read_text()) if args.evaluation_schedule else None
    if schedule:
        schedule.pop("nonce", None)  # random salt so the committed hash cannot be reversed by guessing
    app = App(args.data, args.jobs, transcribe, secrets.token_urlsafe(16), schedule)
    warm = args.data / "warmup.wav"
    silent_wav(warm)
    threading.Thread(target=transcribe, args=(str(warm), None), daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0" if args.lan else "127.0.0.1", args.port), make_handler(app))
    scheme = "https" if args.https else "http"
    if args.https:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(args.data / "tls/server.crt", args.data / "tls/server.key")
        server.socket = ctx.wrap_socket(server.socket, server_side=True, do_handshake_on_connect=False)
    host = socket.gethostname() if args.lan else "localhost"
    print(f"Open {scheme}://{host}:{args.port}/#t={app.token}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
