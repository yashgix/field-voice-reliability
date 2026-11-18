# Visit app (MVP): spoken readings to a checked maintenance record

Local prototype. One technician, one visit at a time, on this Mac. No cloud, no accounts, no LLM, $0.

## What it does
1. **Start a visit** from a job file (`mvp/jobs/*.json`): trade, complaint, equipment, and the checklist of readings.
2. **Capture.** The page asks for one reading at a time. Hold the button to talk, or tap once to start and once to
   stop. The browser records raw audio and sends a 16-bit PCM WAV, so Safari and Chrome behave the same.
3. **Recognise and check.** Whisper turbo with the job record as prompt (never readings), the deterministic parser
   and the reading checker (`fvr/`). A clean reading in the expected unit is accepted.
4. **Clarify.** Otherwise one targeted question: "I heard 9. Is that 9 degrees?", "I heard 118 volts, but suction
   pressure is in psi. What was the reading?", "You corrected yourself. I heard 124. What is the final reading?".
   Answer by voice or tap Yes or No, or type the value. Two unusable answers and the reading is stored as
   **unconfirmed** with its audio kept. A clear "no" is not counted as a failure.
5. **End of visit.** Any checklist reading still missing is listed once: record it now or skip it.
6. **Read-back, one value at a time.** Each value is shown on its own (and spoken if prompts are on) with how it was
   obtained, **Confirm**, **Correct** and **Play what you said**. There is no bulk approval: the visit is saved only
   after the last value is confirmed. Only the value on screen can be confirmed, and the buttons wait 0.6 s after
   each new value, so a double tap cannot approve the next one. A corrected value is checked again.
7. **Record and audit.** Every step is an event in an append-only SQLite log (triggers block UPDATE and DELETE; a hash
   chain exposes edits made around them). Audio clips are stored under their SHA-256. The record
   (`/api/visits/<id>/record`) is rebuilt from events and shows each value's status (accepted, confirmed, corrected,
   unconfirmed, skipped), its origin (automatic, clarified, typed), whether it was corrected or confirmed at read-back,
   who gave it, its recordings and transcripts, every read-back decision with the seconds taken and
   whether the recording was played, and an audit block (chain problems, changed clips, untraceable values).

The system never edits, infers or fills in a value. A value without a unit is only stored after the technician says
yes to the slot's unit. An integer glued to "A" ("60A") is always confirmed, never accepted.

## Run it on the Mac
```sh
scripts/mvp.sh                      # prints http://localhost:8000/#t=<token>; open that address in Chrome or Safari
```
The token in the address is required for every API call and changes each run. Data goes to
`~/field-voice-data/mvp/` (outside git).

## Run it on an iPhone (same Wi-Fi, nothing public)
iPhone Safari only allows the microphone on a secure page, so the app needs HTTPS with a certificate the phone trusts.
1. `scripts/mvp_cert.sh` makes a local certificate authority that is limited (name constraints) to this Mac's name
   and current Wi-Fi address, valid 90 days, and a 30-day server certificate. Keys stay in the data folder.
2. AirDrop `~/field-voice-data/mvp/tls/ca.crt` to the iPhone, install it (Settings, Profile Downloaded), then turn on full trust
   (Settings, General, About, Certificate Trust Settings). This changes what the phone trusts; remove the profile
   after testing (Settings, General, VPN and Device Management).
3. `scripts/mvp.sh --lan --https --port 8443`, then open the printed `https://<mac-name>.local:8443/#t=...` address
   in Safari and allow the microphone. macOS may ask once whether Python may accept incoming connections.
If the microphone is blocked: Settings, Apps, Safari, Microphone, Allow, then reload.

## Tests and checks
| Check | How | Result |
|---|---|---|
| Unit and workflow tests (all pass) | `.venv/bin/python -m pytest` | accept, glued amps, yes/no, "no" never storing the rejected value, ambiguous answers, retries to unconfirmed, failed recognition, wrong unit, two values, bare number, corrections, typed values, missing readings, read-back fix, planted read-back errors from a schedule (only on a different stored value, kept until fixed, never revealed before saving through the readings list, the "Heard" line or the record), one-value-at-a-time read-back (no bulk save, stale or repeated taps refused), dual readings and unparsed unit fragments ("5 m ohms") never proposed as a bare number, a repeated proposal counted toward the retry limit, a usable answer not counted as a failure, spaced "200M Ohms", audio for the wrong slot refused, idempotent uploads, interruptions, closed visits, append-only triggers, tamper detection, clip hashes, WAV validation, token, path traversal, bad lengths and sizes |
| Real Whisper, synthetic voice, full visit | `scripts/mvp_e2e.py` | `results/mvp/e2e.md`: silent clip and an unusable answer retried, "fifty one... fifty eight" heard as **51.58 amps** and accepted, corrected at the per-value read-back and checked again |
| Real browser capture on this Mac | `scripts/mvp_browser_check.py` | `results/mvp/browser-check.md`: headless Chrome pressing the real button, 48 kHz WAV received, "Line voltage is 241V." accepted |
| HTTPS | `scripts/mvp_cert.sh`, then curl with the CA | page and API served over verified TLS; the Wi-Fi address is refused without `--lan`; an idle connection no longer blocks other clients |
| Screens at 390 px and desktop | headless Chrome screenshots | capture and read-back screens fit a phone; a reload resumes the visit |
| Per-value read-back in a real browser | headless Chrome driving the page | Play fetched and played the clip, three fast taps advanced one value, Correct reopened the value, reload resumed mid read-back, saved after the last Confirm |

**Independent review** (a separate reviewer, before the held-out test) found 19 issues. Fixed: a spoken "No, not 118 psi"
stored 118 (critical); the app's own spoken question could be recorded as the answer; audio for one reading could
answer another reading's open question; planted read-back errors could land on wrong values or vanish after another
fix; typed "11.0" not normalised; scorer counting read-back questions and failed first clips; no record of the log's
last hash; the page sticking after a failed request; a TLS handshake blocking the server; bad Content-Length; actions
after a visit closed; pointer capture, the stop window and audio context leaks in the browser; certificate renewal
on a new address; runner cleanup. Not changed: seeds keyed on the visit id (a restart gets a new draw; restarts are
reported).

**Held-out test with planted read-back errors** (results `results/human-mvp/`):
FAIL. 32/32 saved values correct, but 0 of 4 planted read-back errors were caught with the old bulk read-back. The
fixes above came from it; those recordings are now development data.

Evaluation mode shows wrong values from a fixed schedule per job (`--evaluation-schedule`) instead of drawing one at
random per visit.

## Limitations (exact)
- **A wrong value with no trace in the text is accepted.** "Fifty one... fifty eight" became "51.58 amps" and
  "thirty seven... thirty nine" became "37.39 amps", both clean-looking. Only the read-back can catch these, and
  whether a person actually does is not yet measured.
- **Not tested on a real microphone, Safari or an iPhone.** The browser check uses Chrome's fake microphone
  (with its audio service run in-process, because the sandboxed one cannot read the file). Safari on Mac and iPhone
  are untested; the iPhone steps above are written from Apple's documented rules, not tried.
- **Spoken prompts and the microphone:** speech stops when recording starts, and echo cancellation is off so the
  recording is unprocessed. With speakers loud and prompts on, the end of a prompt could still be picked up; it would
  be logged, and a "no" in it can no longer store a value.
- One visit at a time per server; recognition runs one clip at a time (about 1 s per clip on an M4 Pro).
- Readings are captured one checklist slot at a time; free-form dictation of several readings is not supported.
- **Whether the per-value read-back catches wrong values is untested.** More taps do not prove more checking.
- The read-back has not been tested with gloves, glare or noise.
- No login: the per-run token in the address is the only access control. Fine on localhost; on Wi-Fi anyone with the
  address could use it while the server runs.
- No export to any field-service system; the record is JSON from the local API.
- The unit-fits-measurement check is per slot (the slot lists its units); there is no physical plausibility check.
