"""One model call through Claude Code in headless mode on the subscription login, never an API key.

Each call runs with no tools, no settings files, no project files and no customizations, in an empty folder, with a
clean environment, and is refused unless Claude Code reports that no API key was used.
Responses are cached by prompt hash, so a rerun rescores exactly without new calls.
"""

import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


class ModelError(RuntimeError):
    pass


def _claude() -> Path:
    """The official Claude Code binary: LIVE_CLAUDE_BIN, else the newest VS Code extension's."""
    if "LIVE_CLAUDE_BIN" in os.environ:
        return Path(os.environ["LIVE_CLAUDE_BIN"])
    found = sorted(Path.home().glob(".vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude"))
    if not found:
        raise ModelError("no Claude Code binary found, set LIVE_CLAUDE_BIN")
    return max(found, key=lambda p: [int(n) for n in re.findall(r"\d+", p.parts[-4])])


FLAGS = [
    "-p",
    "--safe-mode",
    "--setting-sources",
    "",
    "--tools",
    "",
    "--no-session-persistence",
    "--output-format",
    "stream-json",
    "--verbose",
]


@dataclass
class Reply:
    text: str
    model: str
    seconds: float
    input_tokens: int
    output_tokens: int
    cached: bool


def _env() -> dict:
    return {"HOME": os.environ["HOME"], "PATH": "/usr/bin:/bin", "USER": os.environ.get("USER", "")}


def _parse(stdout: str) -> dict:
    init = result = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line) if line.startswith("{") else {}
        except json.JSONDecodeError as e:
            raise ModelError(f"unreadable output line: {line[:200]}") from e
        if event.get("type") == "system" and event.get("subtype") == "init":
            init = event
        elif event.get("type") == "result":
            result = event
    if init is None or result is None:
        raise ModelError(f"no init or result event: {stdout[-300:]}")
    if init.get("apiKeySource") != "none" or init.get("tools"):
        raise ModelError(f"refusing: auth {init.get('apiKeySource')!r}, tools {init.get('tools')!r}")
    if result.get("is_error"):
        raise ModelError(f"model error: {result.get('result')!r}")
    usage = result["usage"]
    return {
        "text": result["result"],
        "model": init["model"],
        "seconds": result["duration_ms"] / 1000,
        "input_tokens": usage["input_tokens"] + usage["cache_read_input_tokens"] + usage["cache_creation_input_tokens"],
        "output_tokens": usage["output_tokens"],
    }


def call(system: str, prompt: str, model: str, effort: str, cache: Path, salt: str = "") -> Reply:
    """`salt` keeps arms with identical prompts (B's first line equals A-live's) as separate samples."""
    key = hashlib.sha256(json.dumps([model, effort, salt, system, prompt]).encode()).hexdigest()
    hit = cache / f"{key}.json"
    if hit.exists():
        return Reply(**json.loads(hit.read_text()), cached=True)
    with tempfile.TemporaryDirectory() as empty:
        start = time.perf_counter()
        try:
            done = subprocess.run(
                [str(_claude()), *FLAGS, "--model", model, "--effort", effort, "--system-prompt", system],
                input=prompt, capture_output=True, text=True, cwd=empty, env=_env(), timeout=300,
            )  # fmt: skip
        except subprocess.TimeoutExpired as e:
            raise ModelError("call timed out after 300 s") from e
    if done.returncode != 0:
        raise ModelError(f"exit {done.returncode}: {done.stderr[-300:] or done.stdout[-300:]}")
    data = _parse(done.stdout)
    data["seconds"] = round(time.perf_counter() - start, 2)
    cache.mkdir(parents=True, exist_ok=True)
    hit.write_text(json.dumps(data))
    return Reply(**data, cached=False)
