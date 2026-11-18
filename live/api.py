"""One model call through the Anthropic API, with a running spend ledger that refuses calls past a cap.

The key is read from the git-ignored `.env` and never printed. Cost comes from each reply's token counts at the
listed price, and the total is kept in the data folder so the cap holds across runs.
"""

import json
import threading
import time
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parents[1]
MODEL = "claude-haiku-5-5"
PRICE_IN, PRICE_OUT = 0.10e-6, 0.50e-6  # dollars per token, prompts up to 100K tokens
CAP_DOLLARS = 8.0
LEDGER = Path(json.loads((ROOT / "configs/pilot.json").read_text())["work_dir"]).expanduser() / "live/api_spend.json"


class SpendCapReached(RuntimeError):
    pass


def _key() -> str:
    lines = (ROOT / ".env").read_text().splitlines()
    return next(line.split("=", 1)[1].strip() for line in lines if line.startswith("ANTHROPIC_API_KEY="))


class Api:
    """Calls Haiku with thinking off at low effort, for fast record updates."""

    def __init__(self, cap: float = CAP_DOLLARS, ledger: Path = LEDGER):
        self.client = anthropic.Anthropic(api_key=_key(), timeout=20, max_retries=1)  # a stalled call holds the queue
        self.cap, self.ledger, self.lock = cap, ledger, threading.Lock()

    def spent(self) -> float:
        return json.loads(self.ledger.read_text())["dollars"] if self.ledger.exists() else 0.0

    def _add(self, dollars: float) -> None:
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self.ledger.write_text(json.dumps({"dollars": round(self.spent() + dollars, 6)}))

    def __call__(self, system: str, prompt: str) -> tuple[str, dict]:
        with self.lock:
            if self.spent() >= self.cap:
                raise SpendCapReached(f"API spend cap of ${self.cap:.2f} reached")
        start = time.perf_counter()
        reply = self.client.messages.create(
            model=MODEL,
            max_tokens=4000,
            thinking={"type": "disabled"},
            output_config={"effort": "low"},
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = reply.usage
        dollars = usage.input_tokens * PRICE_IN + usage.output_tokens * PRICE_OUT
        with self.lock:
            self._add(dollars)
        text = "".join(block.text for block in reply.content if block.type == "text")
        seconds = round(time.perf_counter() - start, 2)
        meta = {"model": reply.model, "seconds": seconds, "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens, "dollars": round(dollars, 6), "cached": False}  # fmt: skip
        return text, meta
