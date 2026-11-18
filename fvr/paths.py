"""Audio paths are stored relative to the data folder so results and manifests carry no machine-specific paths."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(json.loads((ROOT / "configs/pilot.json").read_text())["data_dir"]).expanduser()


def resolve(path: str) -> str:
    return str(DATA / path) if not Path(path).is_absolute() else path


def portable(path: Path | str) -> str:
    p = Path(path)
    return str(p.relative_to(DATA)) if p.is_absolute() and p.is_relative_to(DATA) else str(p)
