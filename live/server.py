"""Hands-free live mode on this Mac: the page sends each spoken line, the server keeps the job record.

Usage: python -m live.server [--visit live/scenarios/test/g04.json] [--port 8766]
Binds to localhost only. Every API call needs the per-run token printed at start, which the page reads from the URL
fragment, as in the capture app. The job is the visit file's equipment list; its script is never read.
"""

import argparse
import re
import secrets
import threading
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from fvr.paths import DATA
from live.scenario import FIELDS, Visit, load
from live.session import Caller, Session, Transcriber
from mvp.events import ClipStore, EventLog
from mvp.server import MAX_BODY, TYPES, BaseHandler, silent_wav

ROOT = Path(__file__).resolve().parents[1]
FILES = {name: ROOT / "live/static" / name for name in ("index.html", "live.js", "listener.js", "style.css")}
FILES |= {name: ROOT / "mvp/static" / name for name in ("recorder.js", "worklet.js")}
SESSION = re.compile(r"^/api/sessions/([0-9a-f]{12})(/audio|/full|/clips/[0-9a-f]{64})?$")
WHOLE_SESSION_MAX = 200 * 1024 * 1024  # about 35 minutes at 48 kHz


class App:
    def __init__(self, data: Path, visit: Visit, transcribe: Transcriber, ask_model: Caller, token: str):
        data.mkdir(parents=True, exist_ok=True)
        self.log, self.clips = EventLog(data / "events.db"), ClipStore(data / "clips")
        self.visit, self.transcribe, self.ask_model, self.token = visit, transcribe, ask_model, token
        self.sessions: dict[str, Session] = {}

    def start(self) -> Session:
        s = Session(self.visit, self.log, self.clips, self.transcribe, self.ask_model)
        self.sessions[s.id] = s
        return s


def make_handler(app: App) -> type[BaseHandler]:
    class Handler(BaseHandler):
        token = app.token

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if not path.startswith("/api/"):
                name = "index.html" if path == "/" else path.lstrip("/")
                if name not in FILES:
                    return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                return self._send(HTTPStatus.OK, FILES[name].read_bytes(), TYPES[FILES[name].suffix])
            if not self._authorised():
                return None
            if path == "/api/fields":
                return self._json({"fields": FIELDS})
            m = SESSION.match(path)
            session = m and app.sessions.get(m.group(1))
            if not session or m.group(2) in ("/audio", "/full"):
                return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            if m.group(2) is None:
                return self._json(session.state())
            clip = m.group(2).rsplit("/", 1)[1]
            if not session.owns(clip):
                return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return self._send(HTTPStatus.OK, app.clips.path(clip).read_bytes(), "audio/wav")

        def do_POST(self) -> None:
            if not self._authorised():
                return None
            self.max_body = WHOLE_SESSION_MAX if self.path.endswith("/full") else MAX_BODY
            body = self._body()
            if body is None:
                return None
            path = urlparse(self.path).path
            if path == "/api/sessions":
                return self._json(app.start().state(), HTTPStatus.CREATED)
            m = SESSION.match(path)
            session = m and app.sessions.get(m.group(1))
            if not session or m.group(2) not in ("/audio", "/full"):
                return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            if self.headers.get("Content-Type", "") != "audio/wav" or not body.startswith(b"RIFF"):
                return self._json({"error": "send 16-bit PCM WAV"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
            if m.group(2) == "/full":
                return self._json({"clip": session.keep_whole(body)}, HTTPStatus.ACCEPTED)
            return self._json({"line": session.add(body)}, HTTPStatus.ACCEPTED)

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--visit", type=Path, default=ROOT / "live/scenarios/test/g04.json")
    ap.add_argument("--data", type=Path, default=DATA / "live-mode")
    args = ap.parse_args()
    from fvr.asr import load_engine, transcribe

    load_engine()  # on the main thread, before any worker decodes
    from live.api import Api

    app = App(args.data, load(args.visit), transcribe, Api(), secrets.token_urlsafe(16))
    warm = args.data / "warmup.wav"
    silent_wav(warm)
    threading.Thread(target=transcribe, args=(str(warm), None), daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(app))
    print(f"Open http://localhost:{args.port}/#t={app.token}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
