#!/bin/sh
# Start the visit app. Mac only: scripts/mvp.sh   iPhone on the same Wi-Fi: scripts/mvp.sh --lan --https --port 8443
cd "$(dirname "$0")/.."
export PYTHONPATH=. HF_HOME="$HOME/field-voice-data/hf" HF_HUB_OFFLINE=1
exec .venv/bin/python -m mvp.server "$@"
