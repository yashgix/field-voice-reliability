# Human set, post hoc (development data, not held out)

Settings loaded from results/readings_settings.json: Settings(min_prob=0.0, window=4, unit_similarity=0.8).

### human (Yash, post hoc): 40 utterances, 48 readings (all noise conditions)

| Policy | Silent errors (95% CI) | silent wrong | silent missing | Caught / errors | Recall | Precision | False alarms | Utterances interrupted | Questions per reading | Accepted accuracy | Extra latency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 31.2% [17.0, 45.3] | 0 | 15 | 0/15 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.1 ms |
| context | 31.2% [17.0, 45.3] | 0 | 15 | 0/15 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.0 ms |
| rules | 0.0% [0.0, 0.0] | 0 | 0 | 14/14 | 100% | 78% | 4 | 35% | 0.38 | 100.0% | 0.2 ms |
| verifier | 0.0% [0.0, 0.0] | 0 | 0 | 14/14 | 100% | 78% | 4 | 38% | 0.40 | 100.0% | 0.2 ms |
| verifier_2 | 0.0% [0.0, 0.0] | 0 | 0 | 14/14 | 100% | 78% | 4 | 38% | 0.40 | 100.0% | +1 decode (~1 s) |
| always_confirm | 0.0% [0.0, 0.0] | 0 | 0 | 15/15 | 100% | 35% | 28 | 100% | 1.52 | nan% | 0.0 ms |

### human (Yash, post hoc), only lines where every unit was spoken: 29 utterances, 29 readings (all noise conditions)

| Policy | Silent errors (95% CI) | silent wrong | silent missing | Caught / errors | Recall | Precision | False alarms | Utterances interrupted | Questions per reading | Accepted accuracy | Extra latency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 6.9% [0.0, 17.2] | 0 | 2 | 0/2 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.0 ms |
| context | 6.9% [0.0, 17.2] | 0 | 2 | 0/2 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.0 ms |
| rules | 0.0% [0.0, 0.0] | 0 | 0 | 2/2 | 100% | 50% | 2 | 14% | 0.14 | 100.0% | 0.1 ms |
| verifier | 0.0% [0.0, 0.0] | 0 | 0 | 2/2 | 100% | 50% | 2 | 17% | 0.17 | 100.0% | 0.2 ms |
| verifier_2 | 0.0% [0.0, 0.0] | 0 | 0 | 2/2 | 100% | 50% | 2 | 17% | 0.17 | 100.0% | +1 decode (~1 s) |
| always_confirm | 0.0% [0.0, 0.0] | 0 | 0 | 2/2 | 100% | 8% | 23 | 100% | 1.93 | nan% | 0.0 ms |

### human (Yash, post hoc), appliance: 20 utterances, 24 readings (all noise conditions)

| Policy | Silent errors (95% CI) | silent wrong | silent missing | Caught / errors | Recall | Precision | False alarms | Utterances interrupted | Questions per reading | Accepted accuracy | Extra latency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 20.8% [4.3, 38.5] | 0 | 5 | 0/5 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.0 ms |
| context | 20.8% [4.3, 38.5] | 0 | 5 | 0/5 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.0 ms |
| rules | 0.0% [0.0, 0.0] | 0 | 0 | 4/4 | 100% | 57% | 3 | 30% | 0.29 | 100.0% | 0.2 ms |
| verifier | 0.0% [0.0, 0.0] | 0 | 0 | 4/4 | 100% | 57% | 3 | 35% | 0.33 | 100.0% | 0.2 ms |
| verifier_2 | 0.0% [0.0, 0.0] | 0 | 0 | 4/4 | 100% | 57% | 3 | 35% | 0.33 | 100.0% | +1 decode (~1 s) |
| always_confirm | 0.0% [0.0, 0.0] | 0 | 0 | 5/5 | 100% | 26% | 14 | 100% | 1.62 | nan% | 0.0 ms |

### human (Yash, post hoc), quiet: 20 utterances, 24 readings (all noise conditions)

| Policy | Silent errors (95% CI) | silent wrong | silent missing | Caught / errors | Recall | Precision | False alarms | Utterances interrupted | Questions per reading | Accepted accuracy | Extra latency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 41.7% [21.7, 60.7] | 0 | 10 | 0/10 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.0 ms |
| context | 41.7% [21.7, 60.7] | 0 | 10 | 0/10 | 0% | nan% | 0 | 0% | 0.00 | 100.0% | 0.0 ms |
| rules | 0.0% [0.0, 0.0] | 0 | 0 | 10/10 | 100% | 91% | 1 | 40% | 0.46 | 100.0% | 1.1 ms |
| verifier | 0.0% [0.0, 0.0] | 0 | 0 | 10/10 | 100% | 91% | 1 | 40% | 0.46 | 100.0% | 0.2 ms |
| verifier_2 | 0.0% [0.0, 0.0] | 0 | 0 | 10/10 | 100% | 91% | 1 | 40% | 0.46 | 100.0% | +1 decode (~1 s) |
| always_confirm | 0.0% [0.0, 0.0] | 0 | 0 | 10/10 | 100% | 42% | 14 | 100% | 1.42 | nan% | 0.0 ms |
