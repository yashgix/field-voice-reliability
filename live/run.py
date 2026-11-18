"""Run the simple arms on visit scripts in one process, with a hard cap on real calls, and save every call.

Usage: python -m live.run OUT_DIR VISIT.json... --max-calls N [--conditions gold,asr] [--arms A,A-live,B,R]
       [--run 1] [--replies v1|v2|none] [--asr-context none|job] [--model haiku] [--effort low] [--split dev|test]
       [--workers 6]
"""

import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

from live.arms import run_end, run_live
from live.model import ModelError, call
from live.render import NOISE, SNR_DB, job_prompt, redecode, render
from live.scenario import Visit, load

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/pilot.json").read_text())
MAX_TOKENS_PER_CALL = 60_000  # far above the pilot's largest call: anything bigger means something is wrong


class Budget:
    """Counts real (uncached) calls across all threads and stops everything at the cap or on any surprise."""

    def __init__(self, model: str, effort: str, cache: Path, cap: int):
        self.model, self.effort, self.cache, self.cap = model, effort, cache, cap
        self.used, self.stopped, self.lock = 0, None, threading.Lock()

    def caller(self, salt: str):
        return lambda system, prompt: self._call(system, prompt, salt)

    def _reserve(self) -> None:
        with self.lock:
            if self.stopped is None and self.used >= self.cap:
                self.stopped = f"call cap {self.cap} reached"
            if self.stopped:
                raise SystemExit(f"stopped: {self.stopped}")
            self.used += 1

    def _call(self, system: str, prompt: str, salt: str) -> tuple[str, dict]:
        self._reserve()
        try:
            reply = call(system, prompt, self.model, self.effort, self.cache, salt=salt)
            tokens = reply.input_tokens + reply.output_tokens
            if self.model not in reply.model or tokens > MAX_TOKENS_PER_CALL:
                raise ModelError(f"unexpected reply: model {reply.model}, {tokens} tokens")
        except Exception as e:
            self.stopped = str(e)
            raise
        if reply.cached:
            with self.lock:
                self.used -= 1
        return reply.text, {k: v for k, v in asdict(reply).items() if k != "text"}


def run_label(condition: str, context: str, replies: str) -> str:
    """Folder and report label: the first test runs keep their names (asr, gold, asr-unhelpful)."""
    replies = {"helpful": "v1", "unhelpful": "none"}.get(replies, replies)
    suffix = {"v1": "", "none": "-unhelpful"}.get(replies, f"-{replies}")
    return condition + ("" if context in ("none", None) or condition == "gold" else f"+{context}") + suffix


def heard_lines(visit: Visit, condition: str, split: str, context: str = "none") -> dict[str, str]:
    """What the system heard per line. `context` re-decodes the same noisy audio with a job-record prompt."""
    if condition == "gold":
        return {}
    if condition == "voice":  # a real recording, prepared by live.voice --recognise
        voice = Path(CONFIG["work_dir"]).expanduser() / "live" / "voice" / f"{visit.id}.asr.json"
        return {k: v["heard"] for k, v in json.loads(voice.read_text()).items()}
    work = Path(CONFIG["work_dir"]).expanduser() / "live" / f"{split}-{NOISE}-{SNR_DB:g}dB"
    asr = render(visit, split, Path(CONFIG["noise_dir"]).expanduser(), work, CONFIG["synthetic"]["seed"])
    if context != "none":
        prompt = job_prompt(visit, with_fields=context == "job+fields")
        asr = redecode(visit, work, work.with_name(f"{work.name}-{context}"), prompt)
    return {k: v["heard"] for k, v in asr.items()}


def _job(
    visit: Visit, condition: str, heard: dict, arm: str, a: argparse.Namespace, budget: Budget, target: Path
) -> str:
    ask = budget.caller(arm if a.run == 1 else f"{arm}#{a.run}")
    run = run_end(visit, heard, ask) if arm == "A" else run_live(visit, heard, ask, arm, policy=a.replies)
    meta = {"condition": condition, "replies": a.replies, "asr_context": a.asr_context, "run": a.run}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({**meta, "heard": heard, **asdict(run)}, indent=1))
    return f"{visit.id} {condition} {arm}: {len(run.steps)} decisions"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("out", type=Path)
    p.add_argument("visits", nargs="+", type=Path)
    p.add_argument("--max-calls", type=int, required=True)
    p.add_argument("--conditions", default="gold,asr", help="comma list of gold and asr")
    p.add_argument("--arms", default="A,A-live,B,R")
    p.add_argument("--run", type=int, default=1)
    p.add_argument("--replies", default="v1", choices=["v1", "v2", "none"], help="the simulated tech's reply policy")
    p.add_argument("--asr-context", default="none", choices=["none", "job", "job+fields"])
    p.add_argument("--model", default="haiku")
    p.add_argument("--effort", default="low", choices=["low", "medium", "high"])
    p.add_argument("--split", default="dev", choices=["dev", "test"])
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--cache", type=Path, default=Path(CONFIG["work_dir"]).expanduser() / "live/cache")
    a = p.parse_args()
    budget = Budget(a.model, a.effort, a.cache, a.max_calls)
    jobs = []
    for condition in a.conditions.split(","):
        label = run_label(condition, a.asr_context, a.replies)
        for path in a.visits:  # render here, before any thread starts, so no line is voiced twice at once
            visit = load(path)
            heard = heard_lines(visit, condition, a.split, a.asr_context)
            for arm in a.arms.split(","):
                target = a.out / f"run{a.run}" / label / f"{visit.id}.{arm}.json"
                if not target.exists():
                    jobs.append((visit, condition, heard, arm, target))
    with ThreadPoolExecutor(a.workers) as pool:
        for future in [pool.submit(_job, v, c, h, arm, a, budget, t) for v, c, h, arm, t in jobs]:
            try:
                print(future.result(), flush=True)
            except (SystemExit, ModelError) as e:
                print(f"job stopped: {e}", flush=True)
    print(f"{budget.used} new calls" + (f", stopped: {budget.stopped}" if budget.stopped else ""))


if __name__ == "__main__":
    main()
