# Reading reliability: policies compared

Probability floor tuned on dev only: 0.0 (184 dev rows from the two synthetic sets).
Synthetic sets are TTS voices (labelled synthetic). The human set is scored separately (--human, --posthoc).
The rules were written after reading the synthetic (v1) test failures, so that table is optimistic.
Rule changes after the frozen human evaluation came from human-set failures, not from these sets.

### synthetic (test): 52 utterances, 276 readings (all noise conditions)

| Policy | Silent errors (95% CI) | silent wrong | silent missing | Caught / errors | Recall | Precision | False alarms | Utterances interrupted | Questions per reading | Accepted accuracy | Extra latency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 14.9% [8.0, 23.6] | 2 | 39 | 0/41 | 0% | nan% | 0 | 0% | 0.00 | 99.2% | 0.0 ms |
| context | 14.5% [7.7, 23.2] | 3 | 37 | 0/40 | 0% | nan% | 0 | 0% | 0.00 | 98.7% | 0.0 ms |
| rules | 1.4% [0.3, 2.9] | 3 | 1 | 36/40 | 90% | 100% | 0 | 15% | 0.13 | 98.7% | 0.2 ms |
| verifier | 1.4% [0.3, 2.9] | 3 | 1 | 36/40 | 90% | 100% | 0 | 15% | 0.13 | 98.7% | 0.2 ms |
| verifier_2 | 1.1% [0.0, 2.4] | 2 | 1 | 37/40 | 92% | 92% | 3 | 17% | 0.14 | 99.2% | +1 decode (~1 s) |
| always_confirm | 0.0% [0.0, 0.0] | 0 | 0 | 40/40 | 100% | 14% | 236 | 100% | 1.62 | nan% | 0.0 ms |

### readings (test): 80 utterances, 282 readings (all noise conditions)

| Policy | Silent errors (95% CI) | silent wrong | silent missing | Caught / errors | Recall | Precision | False alarms | Utterances interrupted | Questions per reading | Accepted accuracy | Extra latency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 19.9% [12.9, 28.2] | 5 | 51 | 0/56 | 0% | nan% | 0 | 0% | 0.00 | 97.8% | 0.0 ms |
| context | 20.9% [14.2, 29.3] | 4 | 55 | 0/59 | 0% | nan% | 0 | 0% | 0.00 | 98.2% | 0.0 ms |
| rules | 4.6% [1.9, 7.8] | 4 | 9 | 44/57 | 77% | 90% | 5 | 20% | 0.17 | 98.2% | 0.1 ms |
| verifier | 4.3% [1.8, 7.2] | 3 | 9 | 45/57 | 79% | 90% | 5 | 42% | 0.37 | 98.3% | 0.2 ms |
| verifier_2 | 4.3% [1.8, 7.2] | 3 | 9 | 45/57 | 79% | 79% | 12 | 42% | 0.39 | 98.3% | +1 decode (~1 s) |
| always_confirm | 0.0% [0.0, 0.0] | 0 | 0 | 59/59 | 100% | 26% | 169 | 100% | 1.66 | nan% | 0.0 ms |

### readings (test, only lines where every unit was spoken): 67 utterances, 243 readings (all noise conditions)

| Policy | Silent errors (95% CI) | silent wrong | silent missing | Caught / errors | Recall | Precision | False alarms | Utterances interrupted | Questions per reading | Accepted accuracy | Extra latency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 7.0% [3.5, 11.1] | 5 | 12 | 0/17 | 0% | nan% | 0 | 0% | 0.00 | 97.8% | 0.0 ms |
| context | 8.2% [4.4, 12.6] | 4 | 16 | 0/20 | 0% | nan% | 0 | 0% | 0.00 | 98.2% | 0.0 ms |
| rules | 3.7% [1.2, 6.8] | 4 | 5 | 9/18 | 50% | 64% | 5 | 6% | 0.06 | 98.2% | 0.1 ms |
| verifier | 3.3% [1.2, 5.8] | 3 | 5 | 10/18 | 56% | 67% | 5 | 33% | 0.28 | 98.3% | 0.2 ms |
| verifier_2 | 3.3% [1.2, 5.8] | 3 | 5 | 10/18 | 56% | 45% | 12 | 33% | 0.31 | 98.3% | +1 decode (~1 s) |
| always_confirm | 0.0% [0.0, 0.0] | 0 | 0 | 20/20 | 100% | 11% | 169 | 100% | 1.77 | nan% | 0.0 ms |

### dev (both synthetic sets, used for tuning): 56 utterances, 214 readings (all noise conditions)

| Policy | Silent errors (95% CI) | silent wrong | silent missing | Caught / errors | Recall | Precision | False alarms | Utterances interrupted | Questions per reading | Accepted accuracy | Extra latency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 21.0% [12.7, 29.7] | 0 | 45 | 0/45 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.0 ms |
| context | 22.4% [13.8, 31.3] | 0 | 48 | 0/48 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.0 ms |
| rules | 0.0% [0.0, 0.0] | 0 | 0 | 41/41 | 100% | 77% | 12 | 29% | 0.25 | 100.0% | 0.2 ms |
| verifier | 0.0% [0.0, 0.0] | 0 | 0 | 41/41 | 100% | 77% | 12 | 42% | 0.36 | 100.0% | 0.2 ms |
| verifier_2 | 0.0% [0.0, 0.0] | 0 | 0 | 41/41 | 100% | 68% | 19 | 43% | 0.40 | 100.0% | +1 decode (~1 s) |
| always_confirm | 0.0% [0.0, 0.0] | 0 | 0 | 48/48 | 100% | 26% | 140 | 100% | 1.64 | nan% | 0.0 ms |
