# Proposed system: reliable spoken readings for field service

Status key: **built** = exists in this repo and was measured; **proposed** = design only, not built or measured.
This is a design for hands-free field software in general.

## Goal
Turn what a technician says at the equipment into a maintenance record where every reading is either confirmed by the
audio and the transcript, or explicitly confirmed by the technician. No value is ever invented, edited or filled in
from context.

## Data flow
```
audio segment ─► ASR (job context in prompt) ─► transcript + word timings/probabilities
                                                   │
                                                   ▼
                                  measurement parser (value, unit, label, position)
                                                   │
                                                   ▼
                       reading checker ─► accept ──────────────┐
                              │                                 ▼
                              └─► question ─► technician ─► confirmed / corrected / skipped
                                                                 │
job checklist (expected readings) ─► end-of-visit gap prompt ────┤
                                                                 ▼
                                           structured record + audit trail (append-only)
```

## Components
| Component | Status | What it does | Evidence |
|---|---|---|---|
| Job-record context | **built** | Builds a short prompt from the job record: trade, complaint, equipment with model numbers, terms derived from equipment types. Never readings. | Model numbers 65% to 97% exact (synthetic); 0 inserted record values in about 1,450 decodes with stale, wrong or digit-scrambled records. |
| Context selection policy | proposed | Use the record of the job being worked on; skip long generic term lists. | A 32-term generic list caused two repetition loops. |
| ASR | **built** (local) | Whisper large-v3-turbo via mlx-whisper, greedy, no conditioning on previous text. About 6x faster than real time per short clip on an M4 Pro. | Production would need streaming and a server or device budget; not measured. |
| Measurement parser | **built** | Deterministic: numbers in digits or words, trade forms ("one eighteen", "45 over 5", "P S I", "M F D", "24.6A", "50Mohms"), units including inches of water column, microamps, millivolts. Integer + "A" is never parsed (it may be a code). | Parser tests; three independent reviews. |
| Model-number check | **built** | Accept a model number only if it spells a record ID in whole tokens; otherwise ask. | 0 silent model-number errors; 6.4% re-ask with the right record, 45% with a stale one. |
| Reading checker | **built** | Accept, or ask one question for: number with unclear unit, unit-less second value, glued "60A", measurement word with no value, self-correction, approximate value. | Frozen human evaluation passed: 35.4% to 14.6% silent errors, 28% asked. Revised code: synthetic readings test 20.9% to 4.6%, 20% asked (`docs/HUMAN-EVAL-RESULTS.md`). |
| Unit-fits-measurement check | proposed | Resistance must be ohms, pressure psi or inches of water column, etc. | Would catch 4 of the 20 remaining silent errors (found on test; not evaluated). |
| End-of-visit gap prompt | proposed | Compare captured readings with the job type's checklist; ask once for what is missing. | Only realistic answer to a measurement that vanished entirely. |
| Clarification loop | **built** (`mvp/`) | One reading per question, say what is doubtful, accept a short answer, at most two retries, then store as "unconfirmed" with its audio clip. | Voice form-filling practice (VoiceXML, FormBharo). |
| Record and audit trail | **built** (`mvp/events.py`) | Append-only events: audio segment id, raw transcript, parsed reading, checker decision, question, technician answer, final value, model and code version. | Needed so any record value can be traced back to the audio. |

## Boundaries
- The checker sees text, word probabilities and the job record. It never writes a value; only the technician's answer
  or an accepted parse becomes record data.
- The job record shapes recognition (prompt) and model-number checks. It is never a source of readings.
- Integrations to a system of record write only confirmed values, idempotently, keyed by visit and event id.

## Failure modes and handling
| Failure | Seen in | Handling |
|---|---|---|
| Unit misheard ("microtarads", "131C") | synthetic, both sets | ask: "I heard 131 C. What was the unit?" (built) |
| Valid but wrong unit (ohms as volts) | readings set | unit-fits-measurement check (proposed) |
| Number misheard (15 vs 14, 8 vs 80) | first set | partly caught by a second decode (built, +1 decode, small gain); otherwise silent |
| Correction with no cue word ("fifty one... fifty eight" written as one value) | human line 33 | no trace in the text; per-value read-back at the end of the visit (built in `mvp/`) |
| Measurement word destroyed by noise | readings set | no trace in the utterance; end-of-visit gap prompt (proposed) |
| Job context written into the transcript | 5 of about 1,800 context decodes, babble only | model-number check asks; a prompt-overlap check is cheap to add (proposed) |
| Self-correction mangled | babble | correction cue triggers a confirmation when the cue survives (built) |
| Repetition loop from a long prompt | generic list | keep prompts short; compression-ratio guard (proposed) |

## Testing strategy
- Unit tests for every parser and checker rule, including cases where the checker must ask and must stay quiet (built).
- Fixed evaluation sets with dev and test splits; thresholds and rules change only on dev (built).
- Held-out human recordings scored once with frozen code and a pass bar set before recording (built; passed). Those recordings are now development data; the next held-out test needs new ones.
- Before any production use (proposed): real technician audio from glasses and phone microphones across trades,
  per-field error budgets, and an interruption budget agreed with technicians.

## Trade-offs
- Rules over learned detectors: explainable, testable, zero inference cost; they miss errors that leave no trace.
- One decode over two: the second decode bought 0.3 points over the verifier for double the compute.
- Asking over guessing: every question costs the technician time; the measured cost is about one question per five
  readings on synthetic speech, more when corrections and approximate values are confirmed.
- No acoustic gate: the prompt-free likelihood check failed (AUC 0.39), so it is not part of the design.

## Live job record (built, `live/`)
The capture app above takes one reading at a time. A real visit is a conversation across several units, so the live
record works on free speech instead.

```
spoken line ─► Whisper (job record as context) ─► text, unsure words marked
                                                      │
              visit so far (+ the agent's previous record) ─► language model ─► full job record + optional question
                                                      │                                   │
                                                      │                         question ─► technician ─► answer line
                                                      ▼
                       record per unit: readings with the lines they came from, work status, unsettled items
```

| Piece | What it does |
|---|---|
| Record schema | Readings per unit and field, work per unit and task with status (proposed, approved, in progress, done, deferred, declined), nameplate facts, unsettled items, and for each entry the ids of the lines it rests on |
| Designs compared | A: one read of the finished visit. A-live: re-read the visit so far after every line. B: the same plus its own previous record. R: A-live with questions from a fixed rule. +G: plain-code guards (known fields only, a value must appear in its cited words, "done" held one line) |
| Test bench | Visit scripts state what each line changes, so the true record is known after every line. Every record is scored against the truth at that moment, and each error gets one cause. Scripts are sealed by hash before a run |
| Simulated technician | Scripted answers to ambiguities, restatements of recent readings, the nameplate read out, "not sure" for old readings. Replies are voiced and recognised under the same noise |

What the measurements decided: B, the simplest design that keeps its own state, was the best live design, and the
remaining failures were in recognition and in when to ask, not in tracking state. So no heavier memory architecture
was built.
