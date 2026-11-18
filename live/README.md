# Live job record: test bench and live mode

Live mode (hands-free from the microphone) is `session.py`, `server.py` and `static/`; see the main README. The rest of this
folder is the test bench.

Does a model keep a correct job record during a multi-unit HVAC visit, line by line, and where does it fail? Visit
scripts follow [SPEC.md](SPEC.md). Each line says what it changes in the true record, so the truth is known after
every line.

Arms: **A** reads the finished visit once. **A-live** re-reads the visit so far after every spoken line. **B** does the
same and also sees its own previous record. **R** is A-live whose questions come from a fixed rule. **+G** applies plain-code guards to what a live arm proposes (known
fields only, a value must be said in a line it cites, "done" held for one line). Model calls go through Claude Code
in headless mode on the subscription login, with no tools and no project files.

```sh
uv run python -m live.run results/live/pilot live/scenarios/dev/*.json --conditions gold --max-calls 300
uv run python -m live.render live/scenarios/dev/*.json                           # TTS + noise + Whisper, once
uv run python -m live.run results/live/pilot live/scenarios/dev/*.json --conditions asr --max-calls 300
uv run python -m live.run results/live/pilot live/scenarios/dev/*.json --conditions asr --unhelpful --max-calls 300
uv run python -m live.report results/live/pilot live/scenarios/dev/*.json  # add --disputed FILE for test visits
uv run python -m live.agree AUTHOR.json REVIEWER.json                                   # blind label check
```

Responses are cached by prompt in the data folder, so `live.report` and reruns cost no new calls.
