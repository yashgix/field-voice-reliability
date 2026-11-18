# Held-out human evaluation (frozen)

Settings loaded from results/readings_settings.json: Settings(min_prob=0.0, window=4, unit_similarity=0.8).

### human (Yash, held out): 40 utterances, 48 readings (all noise conditions)

| Policy | Silent errors (95% CI) | silent wrong | silent missing | Caught / errors | Recall | Precision | False alarms | Utterances interrupted | Questions per reading | Accepted accuracy | Extra latency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 31.2% [17.0, 45.3] | 0 | 15 | 0/15 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.1 ms |
| context | 35.4% [21.3, 49.1] | 0 | 17 | 0/17 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.0 ms |
| rules | 14.6% [4.3, 26.0] | 0 | 7 | 10/17 | 59% | 83% | 2 | 28% | 0.25 | 100.0% | 0.1 ms |
| verifier | 12.5% [2.3, 23.1] | 0 | 6 | 11/17 | 65% | 85% | 2 | 32% | 0.29 | 100.0% | 0.1 ms |
| verifier_2 | 10.4% [2.1, 20.8] | 0 | 5 | 12/17 | 71% | 80% | 3 | 35% | 0.33 | 100.0% | +1 decode (~1 s) |
| always_confirm | 0.0% [0.0, 0.0] | 0 | 0 | 17/17 | 100% | 40% | 26 | 100% | 1.48 | nan% | 0.0 ms |

### human, appliance: 20 utterances, 24 readings (all noise conditions)

| Policy | Silent errors (95% CI) | silent wrong | silent missing | Caught / errors | Recall | Precision | False alarms | Utterances interrupted | Questions per reading | Accepted accuracy | Extra latency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 20.8% [4.3, 38.5] | 0 | 5 | 0/5 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.0 ms |
| context | 25.0% [8.3, 44.0] | 0 | 6 | 0/6 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.0 ms |
| rules | 16.7% [0.0, 36.0] | 0 | 4 | 2/6 | 33% | 67% | 1 | 15% | 0.12 | 100.0% | 0.1 ms |
| verifier | 16.7% [0.0, 36.0] | 0 | 4 | 2/6 | 33% | 67% | 1 | 20% | 0.17 | 100.0% | 0.1 ms |
| verifier_2 | 12.5% [0.0, 30.8] | 0 | 3 | 3/6 | 50% | 75% | 1 | 25% | 0.21 | 100.0% | +1 decode (~1 s) |
| always_confirm | 0.0% [0.0, 0.0] | 0 | 0 | 6/6 | 100% | 32% | 13 | 100% | 1.58 | nan% | 0.0 ms |

### human, quiet: 20 utterances, 24 readings (all noise conditions)

| Policy | Silent errors (95% CI) | silent wrong | silent missing | Caught / errors | Recall | Precision | False alarms | Utterances interrupted | Questions per reading | Accepted accuracy | Extra latency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 41.7% [21.7, 60.7] | 0 | 10 | 0/10 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.0 ms |
| context | 45.8% [26.1, 64.0] | 0 | 11 | 0/11 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.0 ms |
| rules | 12.5% [0.0, 27.3] | 0 | 3 | 8/11 | 73% | 89% | 1 | 40% | 0.38 | 100.0% | 0.1 ms |
| verifier | 8.3% [0.0, 20.8] | 0 | 2 | 9/11 | 82% | 90% | 1 | 45% | 0.42 | 100.0% | 0.1 ms |
| verifier_2 | 8.3% [0.0, 20.8] | 0 | 2 | 9/11 | 82% | 82% | 2 | 45% | 0.46 | 100.0% | +1 decode (~1 s) |
| always_confirm | 0.0% [0.0, 0.0] | 0 | 0 | 11/11 | 100% | 46% | 13 | 100% | 1.38 | nan% | 0.0 ms |
