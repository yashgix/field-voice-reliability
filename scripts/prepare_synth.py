"""Generate the synthetic job set, TTS audio and noisy mixes. Usage: python scripts/prepare_synth.py"""

import json
import random
from pathlib import Path

from fvr.audio import mix, tts
from fvr.context import CONDITIONS, prompt_for
from fvr.paths import portable
from fvr.synth import as_dict, make_jobs, make_utterances

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/pilot.json").read_text())
WORK = Path(CONFIG["work_dir"]).expanduser()
NOISE = Path(CONFIG["noise_dir"]).expanduser()


def noise_file(split: str, kind: str, seed: int) -> Path:
    folder = NOISE / ("noise_test" if split == "test" else "noise_train")
    files = sorted(folder.glob(f"{kind}_*.wav"))
    return random.Random(seed).choice(files)


def main() -> None:
    syn = CONFIG["synthetic"]
    rng = random.Random(syn["seed"])
    jobs = make_jobs(syn["n_jobs"], rng)
    rows = []
    for i, job in enumerate(jobs):
        split = "dev" if i % syn["dev_every"] == 0 else "test"
        voices = syn["voices"][split]
        for k, utt in enumerate(make_utterances(job, 1 if i % 3 == 0 else 0, rng)):
            voice = voices[(i + k) % len(voices)]
            clean = WORK / "synthetic/clean" / f"{utt.utt_id}.wav"
            tts(utt.spoken_text, voice, clean)
            prompts = {c: prompt_for(c, utt, job, jobs) for c in CONDITIONS}
            for n, (name, kind, snr) in enumerate(CONFIG["noise_conditions"]):
                seed = syn["seed"] + 1000 * i + 10 * k + n
                audio = clean if kind is None else WORK / f"synthetic/{name}/{utt.utt_id}.wav"
                if kind is not None:
                    src = noise_file(split, kind, seed)
                    mix(clean, src, snr, seed, audio)
                rows.append(
                    {
                        **as_dict(utt),
                        "split": split,
                        "voice": voice,
                        "source": "synthetic-tts",
                        "noise": name,
                        "noise_file": None if kind is None else src.name,
                        "snr_db": snr,
                        "mix_seed": seed,
                        "audio": portable(audio),
                        "prompts": prompts,
                    }
                )
    out = ROOT / "results/synthetic/manifest.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    (ROOT / "results/synthetic/jobs.json").write_text(json.dumps([as_dict(j) for j in jobs], indent=1))
    print(f"{len(jobs)} jobs, {len(rows)} audio rows -> {out}")


if __name__ == "__main__":
    main()
