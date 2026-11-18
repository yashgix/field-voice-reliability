"""Real human speech check on VoiceCodeBench segments with product codes or measurements.

The "record" lists the segment's product codes plus four codes from other segments (an order with several items).
The "wrong" record lists five codes from other segments only. Measurements never appear in any context.
Usage: python scripts/prepare_vcb.py
"""

import json
import random
from pathlib import Path

import numpy as np
import soundfile as sf
from mlx_whisper.audio import load_audio

from fvr.audio import SR, mix
from fvr.paths import portable

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/pilot.json").read_text())
VCB = Path(CONFIG["vcb_dir"]).expanduser()
WORK = Path(CONFIG["work_dir"]).expanduser() / "vcb"
NOISE = Path(CONFIG["noise_dir"]).expanduser() / "noise_test"
SEED = 20261116


def record_prompt(codes: list[str]) -> str:
    return "Order record. Items on this order: " + ", ".join(codes) + "."


def main() -> None:
    keep = set((VCB / "subset.txt").read_text().split())
    meta = [json.loads(line) for line in (VCB / "metadata.jsonl").open()]
    meta = [m for m in meta if m["file_name"] in keep]
    all_codes = [(m["audio_id"], e["canonical"]) for m in meta for e in m["entities"] if e["type"] == "product_code"]
    rng = random.Random(SEED)
    noise_files = sorted(NOISE.glob("AirConditioner_*.wav"))
    rows = []
    for i, m in enumerate(meta):
        codes = [e["canonical"] for e in m["entities"] if e["type"] == "product_code"]
        others = [c for a, c in all_codes if a != m["audio_id"]]
        distractors = rng.sample(others, 4)
        record = codes + distractors
        rng.shuffle(record)
        wrong = rng.sample(others, 5)
        clean = WORK / "clean" / f"{m['audio_id']}.wav"
        clean.parent.mkdir(parents=True, exist_ok=True)
        sf.write(clean, np.asarray(load_audio(str(VCB / m["file_name"]))), SR, subtype="PCM_16")
        prompts = {"none": None, "record": record_prompt(record), "wrong": record_prompt(wrong)}
        for name, snr in (("clean", None), ("ac_5", 5)):
            audio = clean
            if snr is not None:
                audio = WORK / name / f"{m['audio_id']}.wav"
                mix(clean, rng.choice(noise_files), snr, SEED + i, audio)
            rows.append(
                {
                    "utt_id": m["audio_id"],
                    "noise": name,
                    "audio": portable(audio),
                    "source": "voicecodebench-human",
                    "speaker": m["speaker"]["id"],
                    "accent": m["speaker"]["accent"],
                    "ref_text": m["transcripts"]["canonical"],
                    "codes": codes,
                    "measurements": [e["canonical"] for e in m["entities"] if e["type"] == "measurement"],
                    "record_codes": record,
                    "wrong_codes": wrong,
                    "prompts": prompts,
                }
            )
    out = ROOT / "results/vcb/manifest.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"{len(meta)} segments, {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
