# Held-out human evaluation: results

Frozen run: the code was frozen before recording and the results were committed unmodified (`results/human/`). Commit
ids in `results/*/FROZEN.txt` refer to the original research history; this repository is a single-commit export.
Everything after "Frozen result" was computed afterwards with the same frozen code and is labelled post hoc.

## Recordings
Yash, iPhone Voice Memos, 16 Nov 2026. Jobs 1 and 2 in a quiet room, jobs 3 and 4 next to a running air duster
(steady noise about 13 to 15 dB below the voice). Job 1 and job 3 were re-recorded once before the run because pauses
inside a line split it in two (checked by piece count only; no audio was listened to or transcribed). 40 of 40 lines
matched, none unmatched.

## Frozen result (pre-registered bar: PASS)
| Policy | Silent errors | 95% CI | Utterances asked |
|---|---|---|---|
| context (job-context Whisper, no checker) | 35.4% (17 of 48) | 21.3 to 49.1 | 0% |
| rules | **14.6%** (7 of 48) | 4.3 to 26.0 | **28%** |
| verifier | 12.5% | 2.3 to 23.1 | 32% |
| verifier_2 | 10.4% | 2.1 to 20.8 | 35% |

Bar: rules at most half of context (17.7%) and fewer than 1 in 3 utterances asked. Both met. Full tables, including
quiet versus appliance, in `results/human/eval.md`.

## Post hoc (frozen code, not part of the bar)
- **Every unit spoken** (pre-registered secondary; the frozen script did not print it): 29 readings, context 13.8%,
  rules 6.9%, 14% asked. Very wide intervals.
- **Without line 33** (Yash reported a slip before seeing results): context 32.6%, rules 10.9%. Still passes.
- **Quiet looked worse than noisy** for context (45.8% vs 25.0%) because jobs 1 and 2 hold most of the readings
  spoken without a unit, not because of noise.
- **0 wrong values accepted, but partly by luck.** On line 33 Yash said "fifty one" then "fifty eight"; Whisper wrote
  "52A on L2" (word probability 0.71). The parser does not read integer amps glued to "A" ("60A", "52A"), so both
  readings counted as missing. With that parser gap fixed, 52 amps would have been accepted silently as a wrong value.
  A self-correction with no cue word is not caught by any current rule.

## The 7 silent errors left by `rules`
| Line | Transcript (job context) | Cause |
|---|---|---|
| 33 (x2) | 60A on L1 and 52A on L2 | parser: integer glued amps; also a wrong value from an uncued self-correction |
| 37 | 50Mohms | parser: glued megohms |
| 7 | 45 over 5 MFT | misheard unit in the "over" form, no question |
| 6 | 44.2 on the helm side and 4.8 on the fan side | only the first unit-less value asked |
| 9 | 120, no wait, 124 | unit-less correction; `rules` has no correction rule (`verifier` does) |
| 27 | houses at 60 | second unit-less value not asked |

False alarms (2): "2nd circuit" read as a number, and "4%" not read as a percent.

## Fixes after the evaluation (post hoc)
Made after the frozen result was committed. The recordings are development data from here on.
Two independent code reviews; the first caught that the first amps fix could invent readings ("Model number 636A"
became 636 amps), the second that new count filters silenced real readings ("Superheat on unit 12"). Both were fixed
before anything was committed. 49 tests (was 30).

- **Glued units:** "50Mohms", "30Ω", Greek "μA" now parse. An integer glued to "A" ("60A") is never accepted: it can be
  amps, a model-number part, a breaker rating or a refrigerant. In a measurement line it gets "I heard 60 A. Is that 60
  amps?"; elsewhere it is left alone.
- **Second readings:** any unit-less number in a measurement line is asked about, including numbers merged with
  "L1"/"T1" or "RLA" like a code. Readings are tracked by position, so a repeated value is no longer dropped. Counts
  ("unit 2", "3 ton") stay quiet unless a measurement word is right before them.
- **Corrections:** a unit-less value after "no wait", "I mean" or "no weight" (a common mishearing) gets one correction
  question for the final value. "No leaks" is no longer a correction cue; "I" is no longer merged into codes.
- **Safety:** `--human` refuses to run once `results/human/FROZEN.txt` exists; post-hoc scoring writes only to
  `results/human-posthoc/`.

### Line 33: what text can and cannot show
Yash said "sixty amps on L one and fifty one... fifty eight on L two". Whisper wrote "60A on L1 and 52A on L2" with
identical text and word probabilities with and without the job record. The transcript holds **no trace of the
correction**, so no rule on the text can tell that 52 is wrong. The revised checker now asks "Is that 52 amps?", but
only because "52A" is an ambiguous glued form. Had Whisper written "52 amps" it would be accepted, correctly by the
rules and wrongly in fact. Only the technician can catch this, which is why the capture app ends every visit with a
read-back of the record (`docs/MVP.md`).

### Original versus revised
| Set | Policy | Silent errors | False alarms | Utterances asked |
|---|---|---|---|---|
| Human, frozen (held out) | context | 35.4% | 0 | 0% |
| Human, frozen (held out) | rules | 14.6% | 2 | 28% |
| Human, revised code (**post hoc**, fixes aimed at these lines) | context | 31.2% | 0 | 0% |
| Human, revised code (**post hoc**) | rules | 0.0% | 4 | 35% |
| Synthetic readings test, original | rules | 5.7% | 11 | 22% |
| Synthetic readings test, revised | rules | 4.6% | 5 | 20% |
| Synthetic readings test, spoken units only, original / revised | rules | 4.5% / 3.7% | 11 / 5 | 9% / 6% |
| Synthetic first test set, original / revised | rules | 1.8% / 1.4% | 0 / 0 | 15% / 15% |

- The human post-hoc 0.0% is expected (the fixes target exactly those lines) and is not evidence. It also asks on 35%
  of utterances, above the 1-in-3 bar.
- The synthetic readings test was not used to design the fixes, with one exception: its false alarms were read before
  the last two fixes ("I mean" and "no weight"). Before that step the revised code had 21 false alarms and asked 27%;
  silent errors were 4.6% either way. So the false-alarm gain is optimistic; the silent-error gain is not.
- Model-number results (all tables in `results/synthetic`, `vcb`, `coala`, `format`) are unchanged.

## What this does and does not show
One speaker, 48 readings, a phone microphone in a home, scripted lines. It supports the design (context plus a
checker that asks) on real speech. It is not evidence about technicians, glasses microphones or job-site noise. The
recordings are now spent as a held-out set: any change tested on them is development, not a new held-out result.
