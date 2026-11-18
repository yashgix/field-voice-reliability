# Findings: job context and spoken readings in field-service speech

15 Nov 2026. Local Whisper large-v3-turbo (mlx-whisper 0.4.3), greedy, temperature 0. $0 API. Every number below is
measured in this repo unless marked **hypothesis**. Tables: `results/synthetic/tables.md` (model numbers),
`results/format/tables.md` (format control), `results/readings_eval.md` (readings), `results/vcb/tables.md` and
`results/coala/tables.md` (real human speech). Synthetic speech is macOS TTS and is labelled as such everywhere.

## Part 2: can silent reading errors be caught without constant interruptions?

**Short answer: partly.** Deterministic rules catch most
readings that leave a trace in the transcript. Much of the headline gain comes from lines where no unit was spoken,
where asking is the right call by design. On lines with every unit spoken the gain is smaller. Human validation was
frozen and its pass bar set before any recording was made.

### What fails (all 40 silent reading errors of the job-context pilot, inspected one by one)
| Cause | Count | Example |
|---|---|---|
| Synthetic-voice pronunciation: "psi" said as a word | 23 | "131 psi" heard as "131C", "141 side" |
| Unit misheard | 13 | "microtarads", "micro ferrers", "1.2M" for amps, "242 holes" |
| Number misheard | 3 | 15 heard as 14, 8 as 80, 116 as 1016 |
| Whole measurement gone | 1 | "people keep now by the sea" (babble noise) |
| Ambiguity or self-correction | 0 | that set had none, so a second set was built |

### What was built (`fvr/readings.py`, with unit tests)
Accept a parsed reading, or ask one question about the whole reading. It never edits, infers or fills a value.
- **unclear unit**: a number after a measurement word, or before a word that sounds like a unit, with no valid unit:
  "I heard 131 C. What was the reading, number and unit?"
- **no value**: a measurement word announced as a value ("superheat is ...") with no number in the clause.
- **correction**: a self-correction cue confirms the corrected value; if nothing parsed, it still asks.
- **approximate**: "about", "maybe", "around" next to a reading.
- **low confidence**: prompt-free word probability under a floor; tuned on dev to 0.0, i.e. off.
- **disagreement** (optional, +1 decode): plain and job-context transcripts disagree.

### Results (synthetic readings set, test split: 80 utterances, 282 readings, 3 noise conditions)
| Policy | All lines: silent errors (95% CI) | Caught | Questions justified | Utterances asked | Lines with every unit spoken: silent errors |
|---|---|---|---|---|---|
| Plain Whisper | 19.9% [12.9, 28.2] | - | - | 0% | - |
| Job-context Whisper (= pilot safeguard for readings) | 20.9% [14.2, 29.3] | 0% | - | 0% | 8.2% [4.4, 12.6] |
| **Rules** | **5.7% [2.5, 9.4]** | 73% | 80% | **22%** | **4.5% [1.6, 7.9]** (45% caught, 9% asked) |
| Verifier (rules + corrections + approximate) | 5.3% [2.2, 9.0] | 75% | 79% | 38% | 4.1% [1.3, 7.5] |
| Verifier + second decode | 5.0% [2.0, 8.4] | 76% | 70% | 39% | - |
| Always confirm | 0% | 100% | 28% | 100% | 0% |

- On lines with every unit spoken (67 utterances, 243 readings) the rules cut silent errors from 8.2% to 4.5%,
  about 45%, with 9% of utterances asked and 11 unneeded questions.
- The second decode adds 0.3 points over the verifier for twice the compute: not worth it here.
- The first synthetic set (whose failures shaped the rules, so optimistic): 14.5% to 1.8% silent.
- Remaining silent errors are mostly readings whose measurement word was destroyed by noise (no rule can see them)
  and valid-but-wrong units (ohms heard as volts).

### Independent review (readings code) and what changed
A second review read the code and recomputed every headline number with its own scorer: the numbers matched. It
also found defects, all fixed with tests before freezing:
- **The extractor could invent values**: adjacent numbers merged ("60, 62 PSI" became 6062 psi; "45/5" became 455;
  "240... 242 volts" became 240242). No synthetic decode had these patterns, but four human script lines would have.
- Lost leading decimals (".72 inches" became 72), "a hundred and fifty" parsed as 50, units missing from the table
  (mV, megaohms, uA, VAC, in-lbs, lower-case p.s.i.), floating-point formatting of values.
- A self-correction with no parsed reading produced no question; unit questions named the possibly wrong number and
  asked only for the unit (now they ask for the whole reading).
- A misheard unit counted as two silent errors (one missing, one spurious); now it is one wrong reading. This and
  the parser fixes moved the readings results from 23.0% to 7.1% (reported earlier) to 20.9% to 5.7%.
- The headline was mostly lines without a spoken unit; the spoken-unit split above is now reported everywhere.
- Two script truth labels were wrong (line 6 first value, line 19); corrected before freezing.
- Known and kept as limits: two test sentences equal two dev sentences word for word; two of the six test voices
  never appear in the readings test; dev/test isolation is consistent with the record but cannot be proven.
No rule was tuned on test failures. The reviewer's findings came from reading code and the script text; no human
audio existed.

### Readings that vanish completely
- Measured: none of the 4,643 decodes in this project came back empty, so mlx-whisper's rule that drops a window
  judged non-speech (no-speech probability above 0.6 with low log-probability) did not cause the missing readings
  here. In longer real recordings it could; log it.
- Literature: no published, evaluated method flags "speech present, no words". Required-slot tracking
  is standard practice (VoiceXML, inspection apps, clinical templates). A second recogniser lowers WER in
  combination but no study measures how many deletions it catches, and it hallucinates too. Voice-activity
  detection should run beside the recogniser, never as a gate (a 2026 preprint saw WER rise from 10.1% to 51.4% on
  whispered speech when VAD gated the audio). Alerts that cry wolf hurt trust more than misses.
- Plan (**proposed**, not built): (1) log every skipped window; (2) an end-of-visit checklist prompt for expected
  readings not captured; (3) voice-activity coverage versus transcript, as a flag only. A second recogniser only if
  (1) to (3) leave a measured gap.

### Context copied into the transcript
In heavy babble noise Whisper sometimes wrote the job prompt instead of the speech ("Equipment on site, model
GMVC636A00"). 5 of about 1,800 context decodes (0.3%), never in quiet or air-conditioner noise.

## Part 1 (pilot): job context and model numbers

1. **Without context** Whisper wrote 65% of spoken model numbers exactly (synthetic, four noise conditions; 53% in
   0 dB air-conditioner noise) and missed 25% of trade terms. Real human speech: 89% of product codes
   (VoiceCodeBench), 40% of rare plant terms missed (COALA).
2. **The job record in the prompt helps**: 97% with the correct record (oracle 98%), 91% with a stale record (same
   brand and series, a few characters different), 64% with another customer's record. Real product codes: small
   effect (89% none, 91% right record, 90% wrong record, 90 codes).
3. **Format-priming control (retracts an earlier claim).** Same record with every model-number digit replaced
   (format right, no digit right): 71.9% vs 65.3% none (+6.6 points, CI 0.0 to 13.8); brand and type only: no gain.
   Stale +26.0, correct +31.6. **Format explains only about a fifth of the gain**; the stale record helps because its
   model numbers share most characters with the correct one. The earlier statement that "most of the gain is
   format" is withdrawn.
4. **No value insertions**: no stale, wrong or digit-scrambled record made Whisper write an unspoken record model
   number (996 synthetic + 256 digit-scrambled + 188 real decodes); COALA 0 of 253 unsaid terms. The 95% upper bound
   is about 3/n per decode.
5. **A long generic vocabulary list caused two repetition loops** (synthetic WER 14.6% to 24.9%; 13.9% without
   them).
6. **Record-match check for model numbers**: 0 silent model-number errors in every arm; re-ask 6.4% with the correct
   record, 45% with a stale or wrong one.
7. **Negative result: the acoustic acceptance gate** (Whisper's prompt-free likelihood of a context-shaped vs plain
   transcript) could not tell helpful from harmful rewrites: AUC 0.39 test, 0.19 dev (0.5 = chance).
8. **Arms (synthetic, correct record):** job-record prompt 90.3% fields right in the transcript, 1.0 s; no context
   76.9%; detect-and-recover 77.3%; hybrid 77.1%.

## Not new (prior work) vs what this adds
Prior work: contextual prompting of Whisper and oracle-list gains (LREC 2026), detect-retrieve-redecode (RECAST,
2609.30694), biased-plus-unbiased ensembles (RefTextLAS), slot validation with capped re-asks in voice form filling
(VoiceXML, FormBharo), self-correction detection. The reading verifier applies known practice; it is not a new
method. What this adds, as far as the searches found: measurements for trade readings in field-like noise, stale and
plausible-wrong records on Whisper with zero observed insertions, a negative result for prompt-free acoustic
acceptance, and an error taxonomy for spoken readings. None of this is an established research result: samples are
small and mostly synthetic.

## Limits
- Synthetic speech dominates. TTS pronunciation causes failures a person would not ("psi" as a word); one voice
  (Flo) accounts for most of the hardest readings-set errors.
- Small samples: 282 test readings, 196 model numbers, 90 real product codes, 28 parsable real measurements.
- Thresholds and rules come from dev data; two rule changes were made after dev failures, none after test failures.
  The readings-set test was scored after those changes, so it is clean for them but was looked at for analysis.
- One model, greedy decoding, no VAD, no streaming, no glasses microphones, no real HVAC rooms.

## Review
An independent review of the scoring code found five defects in part 1 (identifier matching, decimal amps,
silent-miss accounting, long-word codes, unchanged rewrites); all were fixed with tests and everything re-scored.

## Human check
Pass bar, set before recording: on 48 held-out readings from one human speaker, the rules policy has at most half the
silent errors of job-context Whisper, with fewer than 1 in 3 utterances asked. It passed: silent errors fell from
35.4% to 14.6% (all of them readings lost without a question; no wrong value was accepted), with 28% of utterances
asked ([HUMAN-EVAL-RESULTS.md](HUMAN-EVAL-RESULTS.md)).
