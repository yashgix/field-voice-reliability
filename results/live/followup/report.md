
### asr+job, all

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 8 | 8 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 5 | 9 | 57/105 | 15 | 0 | 13 | 2 | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 19589 | 27586 | 17.45 |

### asr+job, ordinary

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 2 | 2 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 2 | 11/24 | 8 | 0 | 7 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4425 | 5185 | 15.61 |

### asr+job, by Claude helper

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 4 | 4 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 1 | 8 | 36/68 | 9 | 0 | 8 | 1 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 9586 | 16587 | 19.81 |

### asr+job, mixed

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 3 | 3 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 5 | 28/42 | 3 | 0 | 3 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 7156 | 10954 | 19.29 |

### asr+job, hard

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 3 | 3 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 5 | 2 | 18/39 | 4 | 0 | 3 | 1 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 8008 | 11447 | 17.45 |

### asr+job, by ChatGPT

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 4 | 4 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 4 | 1 | 21/37 | 6 | 0 | 5 | 1 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 10003 | 10999 | 16.25 |

asr+job: 0 errors on disputed labels, not counted above

### Headroom, asr+job

| visit | run |  |
|---|---|
Exploratory verdict (asr+job): HEADROOM: the best simple arm leaves enough AI-addressable errors in every run. Read it with the spread and the questions.

### asr+job-v2, all

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 8 | 341 | 22 | 9 | 6 | 3 | 2 | 4 | 1 | 15 | 4 | 55 | 514 | 74 | 189 | 3 | 41/105 | 15 | 2 | 13 | 0 | 91 | 1 | 4 | 0 | 53 | 18 | 19 | 0 | 832575 | 958062 | 13.31 |
| A-live+G | 8 | 341 | 20 | 8 | 6 | 2 | 2 | 4 | 1 | 13 | 1 | 59 | 514 | 70 | 0 | 4 | 40/105 | 15 | 2 | 13 | 0 | 91 | 1 | 4 | 0 | 53 | 18 | 19 | 0 | 832575 | 958062 | 13.31 |
| B | 8 | 309 | 5 | 5 | 2 | 3 | 1 | 1 | 2 | 1 | 2 | 16 | 426 | 1 | 213 | 7 | 53/105 | 15 | 4 | 9 | 2 | 59 | 0 | 4 | 0 | 39 | 8 | 12 | 0 | 839156 | 512179 | 8.22 |
| B+G | 8 | 309 | 5 | 5 | 2 | 3 | 1 | 1 | 2 | 1 | 2 | 21 | 426 | 1 | 0 | 7 | 53/105 | 15 | 4 | 9 | 2 | 59 | 0 | 4 | 0 | 39 | 8 | 12 | 0 | 839156 | 512179 | 8.22 |

### asr+job-v2, ordinary

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 2 | 67 | 3 | 2 | 2 | 0 | 0 | 1 | 0 | 2 | 0 | 15 | 103 | 16 | 44 | 2 | 7/24 | 8 | 0 | 8 | 0 | 18 | 0 | 0 | 0 | 9 | 5 | 4 | 0 | 146318 | 157994 | 12.78 |
| A-live+G | 2 | 67 | 3 | 2 | 2 | 0 | 0 | 1 | 0 | 2 | 0 | 16 | 103 | 16 | 0 | 2 | 7/24 | 8 | 0 | 8 | 0 | 18 | 0 | 0 | 0 | 9 | 5 | 4 | 0 | 146318 | 157994 | 12.78 |
| B | 2 | 61 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 37 | 0 | 30 | 1 | 15/24 | 8 | 2 | 5 | 1 | 12 | 0 | 0 | 0 | 10 | 1 | 1 | 0 | 150289 | 71601 | 5.93 |
| B+G | 2 | 61 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 15 | 37 | 0 | 0 | 1 | 15/24 | 8 | 2 | 5 | 1 | 12 | 0 | 0 | 0 | 10 | 1 | 1 | 0 | 150289 | 71601 | 5.93 |

### asr+job-v2, by Claude helper

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 4 | 185 | 16 | 6 | 3 | 3 | 2 | 3 | 1 | 10 | 4 | 55 | 399 | 60 | 107 | 2 | 23/68 | 9 | 2 | 7 | 0 | 60 | 0 | 2 | 0 | 38 | 11 | 11 | 0 | 467336 | 603488 | 14.36 |
| A-live+G | 4 | 185 | 14 | 5 | 3 | 2 | 2 | 3 | 1 | 8 | 1 | 58 | 399 | 57 | 0 | 3 | 22/68 | 9 | 2 | 7 | 0 | 60 | 0 | 2 | 0 | 38 | 11 | 11 | 0 | 467336 | 603488 | 14.36 |
| B | 4 | 161 | 4 | 3 | 1 | 2 | 1 | 1 | 1 | 1 | 2 | 15 | 250 | 0 | 83 | 6 | 36/68 | 9 | 3 | 5 | 1 | 36 | 0 | 2 | 0 | 28 | 2 | 6 | 0 | 453576 | 287122 | 8.87 |
| B+G | 4 | 161 | 4 | 3 | 1 | 2 | 1 | 1 | 1 | 1 | 2 | 18 | 250 | 0 | 0 | 6 | 36/68 | 9 | 3 | 5 | 1 | 36 | 0 | 2 | 0 | 28 | 2 | 6 | 0 | 453576 | 287122 | 8.87 |

### asr+job-v2, mixed

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 3 | 125 | 4 | 5 | 2 | 3 | 2 | 2 | 0 | 0 | 2 | 25 | 158 | 38 | 42 | 0 | 24/42 | 3 | 1 | 2 | 0 | 32 | 0 | 1 | 0 | 20 | 6 | 6 | 0 | 297787 | 353733 | 12.92 |
| A-live+G | 3 | 125 | 4 | 4 | 2 | 2 | 2 | 2 | 0 | 0 | 1 | 28 | 158 | 38 | 0 | 0 | 24/42 | 3 | 1 | 2 | 0 | 32 | 0 | 1 | 0 | 20 | 6 | 6 | 0 | 297787 | 353733 | 12.92 |
| B | 3 | 109 | 1 | 4 | 1 | 3 | 1 | 0 | 0 | 0 | 1 | 1 | 53 | 1 | 21 | 3 | 29/42 | 3 | 1 | 1 | 1 | 16 | 0 | 1 | 0 | 10 | 2 | 4 | 0 | 279788 | 157299 | 7.64 |
| B+G | 3 | 109 | 1 | 4 | 1 | 3 | 1 | 0 | 0 | 0 | 1 | 3 | 53 | 1 | 0 | 3 | 29/42 | 3 | 1 | 1 | 1 | 16 | 0 | 1 | 0 | 10 | 2 | 4 | 0 | 279788 | 157299 | 7.64 |

### asr+job-v2, hard

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 3 | 149 | 15 | 2 | 2 | 0 | 0 | 1 | 1 | 13 | 2 | 15 | 253 | 20 | 103 | 1 | 10/39 | 4 | 1 | 3 | 0 | 41 | 1 | 3 | 0 | 24 | 7 | 9 | 0 | 388470 | 446335 | 13.96 |
| A-live+G | 3 | 149 | 13 | 2 | 2 | 0 | 0 | 1 | 1 | 11 | 0 | 15 | 253 | 16 | 0 | 2 | 9/39 | 4 | 1 | 3 | 0 | 41 | 1 | 3 | 0 | 24 | 7 | 9 | 0 | 388470 | 446335 | 13.96 |
| B | 3 | 139 | 4 | 0 | 0 | 0 | 0 | 1 | 2 | 1 | 1 | 2 | 336 | 0 | 162 | 3 | 9/39 | 4 | 1 | 3 | 0 | 31 | 0 | 3 | 0 | 19 | 5 | 7 | 0 | 409079 | 283279 | 10.55 |
| B+G | 3 | 139 | 4 | 0 | 0 | 0 | 0 | 1 | 2 | 1 | 1 | 3 | 336 | 0 | 0 | 3 | 9/39 | 4 | 1 | 3 | 0 | 31 | 0 | 3 | 0 | 19 | 5 | 7 | 0 | 409079 | 283279 | 10.55 |

### asr+job-v2, by ChatGPT

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 4 | 156 | 6 | 3 | 3 | 0 | 0 | 1 | 0 | 5 | 0 | 0 | 115 | 14 | 82 | 1 | 18/37 | 6 | 0 | 6 | 0 | 31 | 1 | 2 | 0 | 15 | 7 | 8 | 0 | 365239 | 354574 | 12.07 |
| A-live+G | 4 | 156 | 6 | 3 | 3 | 0 | 0 | 1 | 0 | 5 | 0 | 1 | 115 | 13 | 0 | 1 | 18/37 | 6 | 0 | 6 | 0 | 31 | 1 | 2 | 0 | 15 | 7 | 8 | 0 | 365239 | 354574 | 12.07 |
| B | 4 | 148 | 1 | 2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 176 | 1 | 130 | 1 | 17/37 | 6 | 1 | 4 | 1 | 23 | 0 | 2 | 0 | 11 | 6 | 6 | 0 | 385580 | 225057 | 7.64 |
| B+G | 4 | 148 | 1 | 2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 3 | 176 | 1 | 0 | 1 | 17/37 | 6 | 1 | 4 | 1 | 23 | 0 | 2 | 0 | 11 | 6 | 6 | 0 | 385580 | 225057 | 7.64 |

asr+job-v2: 0 errors on disputed labels, not counted above

asr+job-v2: guards on A-live removed 2 live errors and added 0

asr+job-v2: guards on B removed 0 live errors and added 0

### Headroom, asr+job-v2

INCOMPLETE: no run for c01/A, c02/A, c03/A, c04/A, g01/A, g02/A, g03/A, g04/A. No verdict.
