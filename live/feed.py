"""Play a recorded visit into a running live-mode server, line by line at speaking pace, then score the record.

Usage: python -m live.feed "http://localhost:8766/#t=TOKEN" VISIT.json LINES_DIR OUT.json [--gap 1.0]
Each line is sent when it would end in real speech (its length plus the page's 0.7 s pause), then the next starts
after `--gap`. Questions the record asks are logged but not answered: no one is there to answer them.
"""

import argparse
import json
import statistics
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import soundfile as sf

from live.entries import normalize
from live.scenario import load, truth
from live.score import errors, recall

END_PAUSE_S = 0.7  # the page's pause before a line is sent


class Client:
    def __init__(self, url: str):
        u = urlparse(url)
        self.base, self.token = f"{u.scheme}://{u.netloc}", u.fragment.removeprefix("t=")

    def __call__(self, path: str, body: bytes | None = None, kind: str = "application/json") -> dict:
        req = urllib.request.Request(self.base + path, data=body, headers={"X-Token": self.token, "Content-Type": kind})
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read())


def score(visit, state: dict, script_ids: dict[str, str]) -> dict:
    heard = {script_ids[ln["id"]]: ln["heard"] or "" for ln in state["lines"]}
    rec = normalize(state["record"], visit.equipment_ids)
    true = truth(visit.turns)
    hits, total = recall(rec, true, visit.listed)
    wrong = errors(rec, true, visit.turns, heard, visit.listed, final=True)
    return {"hits": hits, "total": total, "wrong": [[*e.key, e.got, e.want, e.cause] for e in wrong],
            "unsettled": sorted(map(str, rec.unresolved))}  # fmt: skip


def latency(state: dict) -> dict:
    times = [ln["recorded_at"] - ln["received"] for ln in state["lines"] if ln["recorded_at"]]
    if len(times) < 2:
        return {}
    model = [u["seconds"] for u in state["updates"]]
    return {"median_s": round(statistics.median(times), 2), "p90_s": round(statistics.quantiles(times, n=10)[-1], 2),
            "max_s": round(max(times), 2), "model_median_s": round(statistics.median(model), 2),
            "plus_pause_s": END_PAUSE_S}  # fmt: skip


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("visit", type=Path)
    p.add_argument("lines", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--gap", type=float, default=1.0)
    a = p.parse_args()
    visit, api = load(a.visit), Client(a.url)
    session = api("/api/sessions", b"{}")["session"]
    script_ids = {}
    for t in (t for t in visit.turns if t.speaker != "device"):
        clip = a.lines / f"{visit.id}-{t.id}.wav"
        time.sleep(sf.info(clip).duration + END_PAUSE_S)
        script_ids[api(f"/api/sessions/{session}/audio", clip.read_bytes(), "audio/wav")["line"]] = t.id
        print(f"sent line {t.id}", flush=True)
        time.sleep(a.gap)
    deadline = time.time() + 120
    while (state := api(f"/api/sessions/{session}"))["waiting"] or any(
        ln["status"] in ("queued", "updating") for ln in state["lines"]
    ):
        if time.time() > deadline or state["error"]:
            break
        time.sleep(0.5)
    result = {"session": session, "script_ids": script_ids, "latency": latency(state), "score": score(visit, state,
              script_ids), "dollars": round(sum(u["dollars"] for u in state["updates"]), 4),
              "updates": len(state["updates"]), "questions": state["questions"], "state": state}  # fmt: skip
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=1))
    print(json.dumps({k: result[k] for k in ("latency", "score", "dollars", "updates", "questions")}, indent=1))


if __name__ == "__main__":
    main()
