#!/bin/sh
# Sequential GPU work for the pilot (one MLX job at a time is faster than two).
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH=. HF_HOME="$HOME/field-voice-data/hf" HF_HUB_OFFLINE=1
.venv/bin/python scripts/run_decodes.py results/synthetic clean,ac_5,ac_0,babble_5
.venv/bin/python scripts/run_arms.py results/synthetic
.venv/bin/python scripts/run_decodes.py results/vcb clean
echo ALL_DONE
