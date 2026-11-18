# Synthetic set results (TTS voices, labelled synthetic)

Test split: 83 utterances x 4 noise conditions.

## Context conditions, all noise levels pooled (test)

| Condition | WER | Term misses | Model-number exact | Reading exact | All fields right | Broke vs none | Fixed vs none | Record IDs inserted | s/decode | Field accuracy vs none (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 14.6% | 25.4% | 65.3% (128/196) | 85.1% (235/276) | 69.0% | 0 | 0 | - | 1.04 | - |
| generic | 24.9% | 23.2% | 62.8% (123/196) | 88.4% (244/276) | 70.5% | 11 | 15 | - | 1.06 | +0.8 pts [-1.7, +3.7] |
| job | 10.3% | 12.7% | 96.9% (190/196) | 85.5% (236/276) | 87.7% | 2 | 65 | 0 | 1.05 | +13.3 pts [+8.0, +19.4] |
| stale | 10.6% | 13.5% | 91.3% (179/196) | 85.5% (236/276) | 84.6% | 7 | 59 | 0 | 1.05 | +11.0 pts [+5.5, +17.0] |
| wrong | 14.6% | 26.2% | 63.8% (125/196) | 84.8% (234/276) | 67.8% | 5 | 1 | 0 | 1.05 | -0.8 pts [-1.9, +0.0] |
| oracle | 11.1% | 12.9% | 98.0% (192/196) | 85.1% (235/276) | 87.7% | 0 | 64 | - | 1.05 | +13.6 pts [+8.5, +19.2] |

### Noise: ac_0

| Condition | WER | Term misses | Model-number exact | Reading exact | All fields right | Broke vs none | Fixed vs none | Record IDs inserted | s/decode | Field accuracy vs none (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 18.4% | 29.4% | 53.1% (26/49) | 79.7% (55/69) | 56.6% | 0 | 0 | - | 1.04 | - |
| generic | 17.5% | 27.0% | 55.1% (27/49) | 85.5% (59/69) | 62.7% | 1 | 6 | - | 1.05 | +4.2 pts [+0.8, +8.4] |
| job | 12.5% | 15.1% | 95.9% (47/49) | 81.2% (56/69) | 83.1% | 0 | 22 | 0 | 1.05 | +18.6 pts [+11.8, +26.1] |
| stale | 12.7% | 15.1% | 91.8% (45/49) | 81.2% (56/69) | 81.9% | 1 | 21 | 0 | 1.05 | +16.9 pts [+10.1, +24.8] |
| wrong | 17.9% | 31.0% | 53.1% (26/49) | 79.7% (55/69) | 56.6% | 1 | 1 | 0 | 1.05 | +0.0 pts [-2.5, +2.4] |
| oracle | 13.6% | 16.7% | 98.0% (48/49) | 79.7% (55/69) | 83.1% | 0 | 22 | - | 1.05 | +18.6 pts [+11.8, +26.2] |

### Noise: ac_5

| Condition | WER | Term misses | Model-number exact | Reading exact | All fields right | Broke vs none | Fixed vs none | Record IDs inserted | s/decode | Field accuracy vs none (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 12.3% | 20.6% | 67.3% (33/49) | 88.4% (61/69) | 72.3% | 0 | 0 | - | 1.04 | - |
| generic | 34.5% | 20.6% | 63.3% (31/49) | 89.9% (62/69) | 72.3% | 4 | 3 | - | 1.07 | -0.8 pts [-6.1, +4.1] |
| job | 8.5% | 7.9% | 95.9% (47/49) | 88.4% (61/69) | 89.2% | 1 | 15 | 0 | 1.05 | +11.9 pts [+6.0, +18.8] |
| stale | 9.1% | 11.1% | 91.8% (45/49) | 88.4% (61/69) | 86.7% | 3 | 15 | 0 | 1.06 | +10.2 pts [+3.9, +17.6] |
| wrong | 13.2% | 22.2% | 63.3% (31/49) | 88.4% (61/69) | 69.9% | 2 | 0 | 0 | 1.05 | -1.7 pts [-4.3, +0.0] |
| oracle | 9.6% | 10.3% | 98.0% (48/49) | 88.4% (61/69) | 90.4% | 0 | 15 | - | 1.05 | +12.7 pts [+7.0, +19.3] |

### Noise: babble_5

| Condition | WER | Term misses | Model-number exact | Reading exact | All fields right | Broke vs none | Fixed vs none | Record IDs inserted | s/decode | Field accuracy vs none (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 19.5% | 35.7% | 63.3% (31/49) | 79.7% (55/69) | 65.1% | 0 | 0 | - | 1.05 | - |
| generic | 38.7% | 31.0% | 57.1% (28/49) | 85.5% (59/69) | 66.3% | 5 | 6 | - | 1.07 | +0.8 pts [-4.7, +6.8] |
| job | 13.8% | 19.8% | 95.9% (47/49) | 79.7% (55/69) | 83.1% | 1 | 17 | 0 | 1.05 | +13.6 pts [+7.1, +20.9] |
| stale | 14.1% | 19.0% | 83.7% (41/49) | 79.7% (55/69) | 75.9% | 2 | 12 | 0 | 1.06 | +8.5 pts [+2.4, +15.5] |
| wrong | 18.8% | 36.5% | 61.2% (30/49) | 78.3% (54/69) | 62.7% | 2 | 0 | 0 | 1.05 | -1.7 pts [-4.3, +0.0] |
| oracle | 14.5% | 15.1% | 95.9% (47/49) | 79.7% (55/69) | 81.9% | 0 | 16 | - | 1.05 | +13.6 pts [+7.9, +20.2] |

### Noise: clean

| Condition | WER | Term misses | Model-number exact | Reading exact | All fields right | Broke vs none | Fixed vs none | Record IDs inserted | s/decode | Field accuracy vs none (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 8.4% | 15.9% | 77.6% (38/49) | 92.8% (64/69) | 81.9% | 0 | 0 | - | 1.04 | - |
| generic | 9.0% | 14.3% | 75.5% (37/49) | 92.8% (64/69) | 80.7% | 1 | 0 | - | 1.05 | -0.8 pts [-2.7, +0.0] |
| job | 6.3% | 7.9% | 100.0% (49/49) | 92.8% (64/69) | 95.2% | 0 | 11 | 0 | 1.05 | +9.3 pts [+4.3, +15.0] |
| stale | 6.5% | 8.7% | 98.0% (48/49) | 92.8% (64/69) | 94.0% | 1 | 11 | 0 | 1.05 | +8.5 pts [+3.3, +14.4] |
| wrong | 8.6% | 15.1% | 77.6% (38/49) | 92.8% (64/69) | 81.9% | 0 | 0 | 0 | 1.05 | +0.0 pts [+0.0, +0.0] |
| oracle | 6.6% | 9.5% | 100.0% (49/49) | 92.8% (64/69) | 95.2% | 0 | 11 | - | 1.05 | +9.3 pts [+4.3, +15.0] |

## Arms with the safeguard (thresholds tuned on dev only)

Thresholds: B: margin 0, min prob 0.0, P: margin 0, min prob 0.0, D: margin 0, min prob 0.0, H: margin 0, min prob 0.0

| Arm | Record | Fields right in text | Silent errors | Caught (wrong, confirmed) | False alarms (right, confirmed) | Re-ask rate | Rewrites kept | Median s |
|---|---|---|---|---|---|---|---|---|
| B | job | 76.9% | 41 (8.7%) | 69 | 16 | 19.6% | 0 | 1.01 |
| P | job | 90.3% | 40 (8.5%) | 6 | 22 | 6.4% | 0 | 1.02 |
| D | job | 77.3% | 41 (8.7%) | 67 | 17 | 19.4% | 10 | 1.10 |
| H | job | 77.1% | 41 (8.7%) | 68 | 16 | 19.4% | 14 | 2.53 |
| B | stale | 76.9% | 41 (8.7%) | 69 | 128 | 45.4% | 0 | 1.01 |
| P | stale | 87.9% | 40 (8.5%) | 17 | 179 | 45.1% | 0 | 1.02 |
| D | stale | 77.3% | 41 (8.7%) | 67 | 130 | 45.4% | 10 | 2.51 |
| H | stale | 77.1% | 41 (8.7%) | 68 | 130 | 45.6% | 15 | 2.53 |
| B | wrong | 76.9% | 41 (8.7%) | 69 | 128 | 45.4% | 0 | 1.01 |
| P | wrong | 76.1% | 42 (8.9%) | 72 | 125 | 45.4% | 0 | 1.02 |
| D | wrong | 76.9% | 41 (8.7%) | 69 | 128 | 45.4% | 3 | 1.03 |
| H | wrong | 76.7% | 41 (8.7%) | 70 | 128 | 45.6% | 22 | 2.53 |

### Arms, noise: ac_0

| Arm | Record | Fields right in text | Silent errors | Caught (wrong, confirmed) | False alarms (right, confirmed) | Re-ask rate | Rewrites kept | Median s |
|---|---|---|---|---|---|---|---|---|
| B | job | 68.6% | 14 (11.9%) | 23 | 3 | 24.5% | 0 | 1.01 |
| P | job | 87.3% | 13 (11.0%) | 2 | 5 | 6.5% | 0 | 1.02 |
| D | job | 68.6% | 14 (11.9%) | 23 | 4 | 25.5% | 1 | 1.20 |
| H | job | 69.5% | 14 (11.9%) | 22 | 3 | 23.6% | 2 | 2.53 |
| B | stale | 68.6% | 14 (11.9%) | 23 | 26 | 46.2% | 0 | 1.01 |
| P | stale | 85.6% | 13 (11.0%) | 4 | 45 | 45.8% | 0 | 1.02 |
| D | stale | 68.6% | 14 (11.9%) | 23 | 26 | 46.2% | 1 | 2.52 |
| H | stale | 69.5% | 14 (11.9%) | 22 | 27 | 46.2% | 2 | 2.52 |
| B | wrong | 68.6% | 14 (11.9%) | 23 | 26 | 46.2% | 0 | 1.01 |
| P | wrong | 68.6% | 14 (11.9%) | 23 | 26 | 46.2% | 0 | 1.02 |
| D | wrong | 68.6% | 14 (11.9%) | 23 | 26 | 46.2% | 1 | 1.03 |
| H | wrong | 68.6% | 14 (11.9%) | 23 | 26 | 46.2% | 5 | 2.53 |

### Arms, noise: ac_5

| Arm | Record | Fields right in text | Silent errors | Caught (wrong, confirmed) | False alarms (right, confirmed) | Re-ask rate | Rewrites kept | Median s |
|---|---|---|---|---|---|---|---|---|
| B | job | 79.7% | 8 (6.8%) | 16 | 4 | 18.2% | 0 | 1.01 |
| P | job | 91.5% | 8 (6.8%) | 2 | 5 | 6.4% | 0 | 1.02 |
| D | job | 79.7% | 8 (6.8%) | 16 | 4 | 18.2% | 4 | 1.16 |
| H | job | 78.8% | 8 (6.8%) | 17 | 3 | 18.2% | 2 | 2.53 |
| B | stale | 79.7% | 8 (6.8%) | 16 | 33 | 44.5% | 0 | 1.01 |
| P | stale | 89.8% | 8 (6.8%) | 4 | 45 | 44.5% | 0 | 1.02 |
| D | stale | 79.7% | 8 (6.8%) | 16 | 33 | 44.5% | 3 | 2.51 |
| H | stale | 78.8% | 8 (6.8%) | 17 | 32 | 44.5% | 3 | 2.53 |
| B | wrong | 79.7% | 8 (6.8%) | 16 | 33 | 44.5% | 0 | 1.01 |
| P | wrong | 78.0% | 8 (6.8%) | 18 | 31 | 44.5% | 0 | 1.02 |
| D | wrong | 79.7% | 8 (6.8%) | 16 | 33 | 44.5% | 0 | 1.02 |
| H | wrong | 78.8% | 8 (6.8%) | 17 | 32 | 44.5% | 5 | 2.52 |

### Arms, noise: babble_5

| Arm | Record | Fields right in text | Silent errors | Caught (wrong, confirmed) | False alarms (right, confirmed) | Re-ask rate | Rewrites kept | Median s |
|---|---|---|---|---|---|---|---|---|
| B | job | 72.9% | 14 (11.9%) | 19 | 4 | 21.9% | 0 | 1.01 |
| P | job | 86.4% | 14 (11.9%) | 2 | 6 | 7.6% | 0 | 1.02 |
| D | job | 72.9% | 14 (11.9%) | 19 | 4 | 21.9% | 3 | 1.10 |
| H | job | 72.9% | 14 (11.9%) | 19 | 5 | 22.9% | 7 | 2.53 |
| B | stale | 72.9% | 14 (11.9%) | 19 | 31 | 47.6% | 0 | 1.01 |
| P | stale | 81.4% | 14 (11.9%) | 8 | 41 | 46.7% | 0 | 1.02 |
| D | stale | 72.9% | 14 (11.9%) | 19 | 31 | 47.6% | 4 | 2.51 |
| H | stale | 72.9% | 14 (11.9%) | 19 | 32 | 48.6% | 7 | 2.52 |
| B | wrong | 72.9% | 14 (11.9%) | 19 | 31 | 47.6% | 0 | 1.01 |
| P | wrong | 71.2% | 15 (12.7%) | 20 | 30 | 47.6% | 0 | 1.01 |
| D | wrong | 72.9% | 14 (11.9%) | 19 | 31 | 47.6% | 2 | 1.02 |
| H | wrong | 72.9% | 14 (11.9%) | 19 | 32 | 48.6% | 9 | 2.52 |

### Arms, noise: clean

| Arm | Record | Fields right in text | Silent errors | Caught (wrong, confirmed) | False alarms (right, confirmed) | Re-ask rate | Rewrites kept | Median s |
|---|---|---|---|---|---|---|---|---|
| B | job | 86.4% | 5 (4.2%) | 11 | 5 | 14.2% | 0 | 1.02 |
| P | job | 95.8% | 5 (4.2%) | 0 | 6 | 5.3% | 0 | 1.02 |
| D | job | 88.1% | 5 (4.2%) | 9 | 5 | 12.4% | 2 | 1.05 |
| H | job | 87.3% | 5 (4.2%) | 10 | 5 | 13.3% | 3 | 2.55 |
| B | stale | 86.4% | 5 (4.2%) | 11 | 38 | 43.4% | 0 | 1.02 |
| P | stale | 94.9% | 5 (4.2%) | 1 | 48 | 43.4% | 0 | 1.02 |
| D | stale | 88.1% | 5 (4.2%) | 9 | 40 | 43.4% | 2 | 2.52 |
| H | stale | 87.3% | 5 (4.2%) | 10 | 39 | 43.4% | 3 | 2.54 |
| B | wrong | 86.4% | 5 (4.2%) | 11 | 38 | 43.4% | 0 | 1.02 |
| P | wrong | 86.4% | 5 (4.2%) | 11 | 38 | 43.4% | 0 | 1.02 |
| D | wrong | 86.4% | 5 (4.2%) | 11 | 38 | 43.4% | 0 | 1.03 |
| H | wrong | 86.4% | 5 (4.2%) | 11 | 38 | 43.4% | 3 | 2.54 |

## Acoustic acceptance signals (0.5 = chance)

| Split | Rewrites that fix fields | Rewrites that break fields | AUC, whole-transcript score gap | AUC, lowest prompt-free word probability among changed words |
|---|---|---|---|---|
| dev | 59 | 3 | 0.19 | 0.32 |
| test | 232 | 26 | 0.39 | 0.54 |
