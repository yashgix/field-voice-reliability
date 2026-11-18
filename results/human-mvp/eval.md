# Held-out human evaluation of the visit app (frozen)

Visits scored: 4 of 4; not counted: 0. Readings: 32.

| | Correct | Silent wrong | Silent missing | Flagged (unconfirmed or skipped) |
|---|---|---|---|---|
| Visit app | 32 | 0 | 0 | 0 |
| Baseline: job-context Whisper, no checker | 22 | 0 | 10 | - |

Questions before the read-back: 14 (0.44 per reading).
Planted read-back errors on correct values caught: 0 of 4 [{'actual': '11', 'shown': '15', 'slot': 'superheat', 'caught': False}, {'actual': '118', 'shown': '115', 'slot': 'outlet_temp', 'caught': False}, {'actual': '1.1', 'shown': '1.5', 'slot': 'neutral_ground', 'caught': False}, {'actual': '3.1', 'shown': '3.6', 'slot': 'flame_sensor', 'caught': False}].
Planted errors that landed on an already wrong value: 0 of 0 [].
Wrong values stored at the first read-back, caught: 0 of 0 [].
Median visit length: 3.5 min.
Audit chain problems: none. Event log: 108 events, last hash 20c7ee455edb6958814d215637dad95a0b38559e7cdf267733fd52de8aa29495, events.db SHA-256 6e7c233b5ba1c7d01d0b46f135733a76d8b3c0e29cd1ee6c1ac0877329d3f455.

## Pre-registered bar

- PASS: silent wrong values in the record at most 1 of 32
- PASS: silent wrong values at most half of the no-checker baseline
- PASS: unconfirmed or skipped at most 10% of readings
- PASS: at most 0.5 questions per reading before the read-back
- FAIL: every planted read-back error caught
- PASS: audit intact and every value traceable
- PASS: all 4 visits completed

Overall: FAIL

## By reading type

| Type | Readings | Correct | Silent wrong | Flagged | Questions | Baseline correct |
|---|---|---|---|---|---|---|
| approximate_no_unit | 1 | 1 | 0 | 0 | 1 | 0 |
| cued_correction | 1 | 1 | 0 | 0 | 1 | 1 |
| no_unit | 3 | 3 | 0 | 0 | 3 | 0 |
| plain | 23 | 23 | 0 | 0 | 4 | 19 |
| uncued_correction | 4 | 4 | 0 | 0 | 5 | 2 |
