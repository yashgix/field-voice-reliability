"""Exploratory: A (one end-of-visit read) over B's full live transcript, including the tech's replies."""

import glob
import json
from dataclasses import asdict, replace
from pathlib import Path

from live.arms import run_end
from live.run import CONFIG, Budget
from live.scenario import Turn, load

budget = Budget("haiku", "low", Path(CONFIG["work_dir"]).expanduser() / "live/cache", 8)
out = Path("results/live/followup-final/run1/asr+job-v2")
out.mkdir(parents=True, exist_ok=True)
for f in sorted(glob.glob("live/scenarios/test/[cg]0?.json")):
    v = load(f)
    b = json.load(open(f"results/live/followup/run1/asr+job-v2/{v.id}.B.json"))
    turns = [Turn(**t) for t in b["turns"]]
    run = run_end(replace(v, turns=turns), b["heard"], budget.caller("A-final"))
    meta = {"condition": "asr", "replies": "v2", "asr_context": "job", "run": 1, "source": "B transcript"}
    (out / f"{v.id}.A.json").write_text(json.dumps({**meta, "heard": b["heard"], **asdict(run)}, indent=1))
    print(v.id, run.steps[0].reply["model"], flush=True)
print(budget.used, "new calls", budget.stopped or "")
