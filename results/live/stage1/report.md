
### asr, all

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 8 | 324 | 14 | 23 | 15 | 8 | 1 | 2 | 6 | 5 | 1 | 61 | 526 | 80 | 234 | 6 | 45/105 | 14 | 1 | 11 | 2 | 74 | 1 | 4 | 22 | 51 | 0 | 760321 | 908466 | 13.31 |
| A-live+G | 8 | 324 | 14 | 22 | 15 | 7 | 1 | 2 | 6 | 5 | 0 | 70 | 526 | 72 | 0 | 6 | 44/105 | 14 | 1 | 11 | 2 | 74 | 1 | 4 | 22 | 51 | 0 | 760321 | 908466 | 13.31 |
| A | 8 | 8 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 3 | 8 | 57/105 | 14 | 0 | 12 | 2 | 0 | 0 | 4 | 0 | 0 | 0 | 19483 | 25970 | 15.41 |
| B | 8 | 324 | 3 | 4 | 2 | 2 | 0 | 1 | 0 | 2 | 1 | 47 | 539 | 2 | 212 | 5 | 50/105 | 14 | 1 | 12 | 1 | 74 | 3 | 4 | 28 | 43 | 0 | 886945 | 545281 | 8.48 |
| B+G | 8 | 324 | 3 | 4 | 2 | 2 | 0 | 1 | 0 | 2 | 1 | 50 | 539 | 2 | 0 | 5 | 49/105 | 14 | 1 | 12 | 1 | 74 | 3 | 4 | 28 | 43 | 0 | 886945 | 545281 | 8.48 |
| R | 8 | 285 | 36 | 29 | 22 | 7 | 1 | 10 | 7 | 18 | 5 | 79 | 267 | 60 | 70 | 9 | 57/105 | 14 | 1 | 11 | 2 | 35 | 2 | 4 | 16 | 17 | 0 | 619540 | 715072 | 12.08 |
| R+G | 8 | 285 | 34 | 28 | 22 | 6 | 1 | 9 | 7 | 17 | 2 | 90 | 267 | 59 | 0 | 9 | 56/105 | 14 | 0 | 12 | 2 | 35 | 2 | 4 | 16 | 17 | 0 | 619540 | 715072 | 12.08 |

### asr, ordinary

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 2 | 67 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 23 | 145 | 9 | 50 | 1 | 5/24 | 7 | 0 | 7 | 0 | 18 | 0 | 0 | 5 | 13 | 0 | 146769 | 161135 | 12.73 |
| A-live+G | 2 | 67 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 24 | 145 | 6 | 0 | 1 | 5/24 | 7 | 0 | 7 | 0 | 18 | 0 | 0 | 5 | 13 | 0 | 146769 | 161135 | 12.73 |
| A | 2 | 2 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 2 | 12/24 | 7 | 0 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4409 | 5468 | 15.1 |
| B | 2 | 67 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 24 | 67 | 0 | 70 | 1 | 8/24 | 7 | 1 | 6 | 0 | 18 | 0 | 0 | 8 | 10 | 0 | 166860 | 90675 | 7.67 |
| B+G | 2 | 67 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 24 | 67 | 0 | 0 | 1 | 8/24 | 7 | 1 | 6 | 0 | 18 | 0 | 0 | 8 | 10 | 0 | 166860 | 90675 | 7.67 |
| R | 2 | 55 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 22 | 48 | 9 | 15 | 1 | 13/24 | 7 | 1 | 6 | 0 | 6 | 0 | 0 | 4 | 2 | 0 | 110119 | 109155 | 11.15 |
| R+G | 2 | 55 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 25 | 48 | 9 | 0 | 1 | 12/24 | 7 | 0 | 7 | 0 | 6 | 0 | 0 | 4 | 2 | 0 | 110119 | 109155 | 11.15 |

### asr, by Claude helper

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 4 | 171 | 3 | 23 | 15 | 8 | 1 | 2 | 0 | 0 | 1 | 60 | 302 | 51 | 94 | 5 | 32/68 | 8 | 1 | 5 | 2 | 46 | 0 | 2 | 17 | 29 | 0 | 404074 | 549169 | 15.01 |
| A-live+G | 4 | 171 | 3 | 22 | 15 | 7 | 1 | 2 | 0 | 0 | 0 | 68 | 302 | 44 | 0 | 5 | 31/68 | 8 | 1 | 5 | 2 | 46 | 0 | 2 | 17 | 29 | 0 | 404074 | 549169 | 15.01 |
| A | 4 | 4 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 1 | 7 | 37/68 | 8 | 0 | 6 | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 9510 | 15419 | 18.04 |
| B | 4 | 169 | 2 | 4 | 2 | 2 | 0 | 1 | 0 | 1 | 1 | 33 | 331 | 0 | 63 | 4 | 37/68 | 8 | 1 | 6 | 1 | 44 | 1 | 2 | 21 | 22 | 0 | 481340 | 320660 | 9.0 |
| B+G | 4 | 169 | 2 | 4 | 2 | 2 | 0 | 1 | 0 | 1 | 1 | 35 | 331 | 0 | 0 | 4 | 36/68 | 8 | 1 | 6 | 1 | 44 | 1 | 2 | 21 | 22 | 0 | 481340 | 320660 | 9.0 |
| R | 4 | 147 | 18 | 24 | 18 | 6 | 1 | 8 | 1 | 8 | 3 | 54 | 200 | 42 | 30 | 6 | 38/68 | 8 | 1 | 5 | 2 | 22 | 0 | 2 | 13 | 9 | 0 | 319309 | 426297 | 13.55 |
| R+G | 4 | 147 | 18 | 22 | 18 | 4 | 1 | 8 | 1 | 8 | 1 | 60 | 200 | 41 | 0 | 6 | 37/68 | 8 | 0 | 6 | 2 | 22 | 0 | 2 | 13 | 9 | 0 | 319309 | 426297 | 13.55 |

### asr, mixed

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 3 | 119 | 3 | 15 | 9 | 6 | 1 | 2 | 0 | 0 | 0 | 2 | 197 | 39 | 65 | 4 | 24/42 | 3 | 0 | 2 | 1 | 26 | 0 | 1 | 9 | 17 | 0 | 270829 | 320479 | 13.28 |
| A-live+G | 3 | 119 | 3 | 15 | 9 | 6 | 1 | 2 | 0 | 0 | 0 | 3 | 197 | 34 | 0 | 4 | 24/42 | 3 | 0 | 2 | 1 | 26 | 0 | 1 | 9 | 17 | 0 | 270829 | 320479 | 13.28 |
| A | 3 | 3 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 5 | 29/42 | 3 | 0 | 2 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 7107 | 9367 | 15.35 |
| B | 3 | 114 | 2 | 3 | 1 | 2 | 0 | 1 | 0 | 1 | 1 | 0 | 168 | 1 | 15 | 3 | 27/42 | 3 | 0 | 3 | 0 | 21 | 1 | 1 | 10 | 10 | 0 | 299763 | 183189 | 7.78 |
| B+G | 3 | 114 | 2 | 3 | 1 | 2 | 0 | 1 | 0 | 1 | 1 | 2 | 168 | 1 | 0 | 3 | 27/42 | 3 | 0 | 3 | 0 | 21 | 1 | 1 | 10 | 10 | 0 | 299763 | 183189 | 7.78 |
| R | 3 | 100 | 17 | 16 | 9 | 7 | 1 | 8 | 6 | 2 | 3 | 3 | 70 | 23 | 9 | 5 | 26/42 | 3 | 0 | 3 | 0 | 7 | 0 | 1 | 4 | 3 | 0 | 208605 | 225792 | 11.73 |
| R+G | 3 | 100 | 17 | 14 | 9 | 5 | 1 | 8 | 6 | 2 | 1 | 6 | 70 | 23 | 0 | 5 | 26/42 | 3 | 0 | 3 | 0 | 7 | 0 | 1 | 4 | 3 | 0 | 208605 | 225792 | 11.73 |

### asr, hard

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 3 | 138 | 10 | 8 | 6 | 2 | 0 | 0 | 6 | 4 | 1 | 36 | 184 | 32 | 119 | 1 | 16/39 | 4 | 1 | 2 | 1 | 30 | 1 | 3 | 8 | 21 | 0 | 342723 | 426852 | 14.27 |
| A-live+G | 3 | 138 | 10 | 7 | 6 | 1 | 0 | 0 | 6 | 4 | 0 | 43 | 184 | 32 | 0 | 1 | 15/39 | 4 | 1 | 2 | 1 | 30 | 1 | 3 | 8 | 21 | 0 | 342723 | 426852 | 14.27 |
| A | 3 | 3 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 3 | 1 | 16/39 | 4 | 0 | 3 | 1 | 0 | 0 | 3 | 0 | 0 | 0 | 7967 | 11135 | 15.43 |
| B | 3 | 143 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 23 | 304 | 1 | 127 | 1 | 15/39 | 4 | 0 | 3 | 1 | 35 | 2 | 3 | 10 | 23 | 0 | 420322 | 271417 | 9.39 |
| B+G | 3 | 143 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 24 | 304 | 1 | 0 | 1 | 14/39 | 4 | 0 | 3 | 1 | 35 | 2 | 3 | 10 | 23 | 0 | 420322 | 271417 | 9.39 |
| R | 3 | 130 | 17 | 13 | 13 | 0 | 0 | 2 | 1 | 14 | 2 | 54 | 149 | 28 | 46 | 3 | 18/39 | 4 | 0 | 2 | 2 | 22 | 2 | 3 | 8 | 12 | 0 | 300816 | 380125 | 13.55 |
| R+G | 3 | 130 | 15 | 14 | 13 | 1 | 0 | 1 | 1 | 13 | 1 | 59 | 149 | 27 | 0 | 3 | 18/39 | 4 | 0 | 2 | 2 | 22 | 2 | 3 | 8 | 12 | 0 | 300816 | 380125 | 13.55 |

### asr, by ChatGPT

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 4 | 153 | 11 | 0 | 0 | 0 | 0 | 0 | 6 | 5 | 0 | 1 | 224 | 29 | 140 | 1 | 13/37 | 6 | 0 | 6 | 0 | 28 | 1 | 2 | 5 | 22 | 0 | 356247 | 359297 | 11.88 |
| A-live+G | 4 | 153 | 11 | 0 | 0 | 0 | 0 | 0 | 6 | 5 | 0 | 2 | 224 | 28 | 0 | 1 | 13/37 | 6 | 0 | 6 | 0 | 28 | 1 | 2 | 5 | 22 | 0 | 356247 | 359297 | 11.88 |
| A | 4 | 4 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 2 | 1 | 20/37 | 6 | 0 | 6 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 9973 | 10551 | 15.41 |
| B | 4 | 155 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 14 | 208 | 2 | 149 | 1 | 13/37 | 6 | 0 | 6 | 0 | 30 | 2 | 2 | 7 | 21 | 0 | 405605 | 224621 | 7.82 |
| B+G | 4 | 155 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 15 | 208 | 2 | 0 | 1 | 13/37 | 6 | 0 | 6 | 0 | 30 | 2 | 2 | 7 | 21 | 0 | 405605 | 224621 | 7.82 |
| R | 4 | 138 | 18 | 5 | 4 | 1 | 0 | 2 | 6 | 10 | 2 | 25 | 67 | 18 | 40 | 3 | 19/37 | 6 | 0 | 6 | 0 | 13 | 2 | 2 | 3 | 8 | 0 | 300231 | 288775 | 10.64 |
| R+G | 4 | 138 | 16 | 6 | 4 | 2 | 0 | 1 | 6 | 9 | 1 | 30 | 67 | 18 | 0 | 3 | 19/37 | 6 | 0 | 6 | 0 | 13 | 2 | 2 | 3 | 8 | 0 | 300231 | 288775 | 10.64 |

asr: 0 errors on disputed labels, not counted above

asr: guards on A-live removed 1 live errors and added 0

asr: guards on B removed 0 live errors and added 0

asr: guards on R removed 2 live errors and added 0

### Headroom, asr

| visit | run | A-live | A-live+G | B | B+G | R | R+G |
|---|---|---|---|---|---|---|---|
| c01 | 1 | 0 | 0 | 0 | 0 | 1 | 1 |
| c02 | 1 | 2 | 2 | 1 | 1 | 7 | 7 |
| c03 | 1 | 1 | 1 | 1 | 1 | 4 | 4 |
| c04 | 1 | 0 | 0 | 0 | 0 | 6 | 6 |
| g01 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| g02 | 1 | 0 | 0 | 0 | 0 | 6 | 6 |
| g03 | 1 | 10 | 10 | 0 | 0 | 9 | 8 |
| g04 | 1 | 0 | 0 | 0 | 0 | 2 | 1 |

Run 1: best simple arm B with 3: errors in 3 of 8 visits (c02, c03, g01), by type {'ordinary': 1, 'mixed': 2, 'hard': 0}, 74 questions of which 43 needless
Exploratory verdict (asr): NO HEADROOM: the best simple arm leaves too few AI-addressable errors in every run. Read it with the spread and the questions.

### gold, all

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 8 | 284 | 21 | 0 | 0 | 0 | 0 | 20 | 0 | 1 | 0 | 0 | 211 | 27 | 62 | 1 | 97/105 | 0 | 0 | 0 | 0 | 34 | 4 | 4 | 10 | 20 | 0 | 617951 | 545083 | 9.32 |
| A-live+G | 8 | 284 | 21 | 0 | 0 | 0 | 0 | 20 | 0 | 1 | 0 | 10 | 211 | 25 | 0 | 1 | 92/105 | 0 | 0 | 0 | 0 | 34 | 4 | 4 | 10 | 20 | 0 | 617951 | 545083 | 9.32 |
| A | 8 | 8 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 3 | 101/105 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 18610 | 18210 | 10.44 |
| B | 8 | 277 | 7 | 0 | 0 | 0 | 0 | 6 | 0 | 1 | 0 | 0 | 180 | 0 | 27 | 6 | 95/105 | 0 | 0 | 0 | 0 | 27 | 4 | 4 | 7 | 16 | 0 | 709782 | 332870 | 6.47 |
| B+G | 8 | 277 | 7 | 0 | 0 | 0 | 0 | 6 | 0 | 1 | 0 | 11 | 180 | 0 | 0 | 6 | 89/105 | 0 | 0 | 0 | 0 | 27 | 4 | 4 | 7 | 16 | 0 | 709782 | 332870 | 6.47 |
| R | 8 | 256 | 19 | 0 | 0 | 0 | 1 | 17 | 0 | 1 | 0 | 0 | 45 | 32 | 3 | 3 | 101/105 | 0 | 0 | 0 | 0 | 6 | 2 | 4 | 0 | 4 | 0 | 522658 | 397670 | 7.88 |
| R+G | 8 | 256 | 19 | 0 | 0 | 0 | 1 | 17 | 0 | 1 | 0 | 13 | 45 | 30 | 0 | 3 | 96/105 | 0 | 0 | 0 | 0 | 6 | 2 | 4 | 0 | 4 | 0 | 522658 | 397670 | 7.88 |

### gold, ordinary

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 2 | 50 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 6 | 0 | 0 | 0 | 23/24 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 95525 | 46490 | 5.25 |
| A-live+G | 2 | 50 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 3 | 6 | 0 | 0 | 0 | 22/24 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 95525 | 46490 | 5.25 |
| A | 2 | 2 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 24/24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4234 | 2659 | 8.08 |
| B | 2 | 54 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 61 | 0 | 15 | 1 | 23/24 | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 2 | 3 | 0 | 126345 | 50071 | 5.49 |
| B+G | 2 | 54 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 61 | 0 | 0 | 1 | 22/24 | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 2 | 3 | 0 | 126345 | 50071 | 5.49 |
| R | 2 | 49 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 2 | 1 | 1 | 1 | 24/24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 93136 | 45950 | 5.66 |
| R+G | 2 | 49 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 3 | 2 | 1 | 0 | 1 | 23/24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 93136 | 45950 | 5.66 |

### gold, by Claude helper

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 4 | 132 | 19 | 0 | 0 | 0 | 0 | 19 | 0 | 0 | 0 | 0 | 71 | 24 | 19 | 1 | 67/68 | 0 | 0 | 0 | 0 | 7 | 2 | 2 | 1 | 4 | 0 | 275520 | 256369 | 8.92 |
| A-live+G | 4 | 132 | 19 | 0 | 0 | 0 | 0 | 19 | 0 | 0 | 0 | 6 | 71 | 22 | 0 | 1 | 62/68 | 0 | 0 | 0 | 0 | 7 | 2 | 2 | 1 | 4 | 0 | 275520 | 256369 | 8.92 |
| A | 4 | 4 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 3 | 64/68 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 9197 | 9999 | 10.44 |
| B | 4 | 129 | 6 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 5 | 61/68 | 0 | 0 | 0 | 0 | 4 | 2 | 2 | 0 | 2 | 0 | 329311 | 146255 | 5.69 |
| B+G | 4 | 129 | 6 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 5 | 55/68 | 0 | 0 | 0 | 0 | 4 | 2 | 2 | 0 | 2 | 0 | 329311 | 146255 | 5.69 |
| R | 4 | 129 | 18 | 0 | 0 | 0 | 1 | 17 | 0 | 0 | 0 | 0 | 24 | 27 | 2 | 2 | 65/68 | 0 | 0 | 0 | 0 | 4 | 0 | 2 | 0 | 4 | 0 | 262428 | 222863 | 8.39 |
| R+G | 4 | 129 | 18 | 0 | 0 | 0 | 1 | 17 | 0 | 0 | 0 | 7 | 24 | 25 | 0 | 2 | 60/68 | 0 | 0 | 0 | 0 | 4 | 0 | 2 | 0 | 4 | 0 | 262428 | 222863 | 8.39 |

### gold, mixed

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 3 | 109 | 18 | 0 | 0 | 0 | 0 | 18 | 0 | 0 | 0 | 0 | 124 | 22 | 42 | 1 | 36/42 | 0 | 0 | 0 | 0 | 16 | 1 | 1 | 3 | 12 | 0 | 235204 | 232732 | 10.12 |
| A-live+G | 3 | 109 | 18 | 0 | 0 | 0 | 0 | 18 | 0 | 0 | 0 | 1 | 124 | 20 | 0 | 1 | 33/42 | 0 | 0 | 0 | 0 | 16 | 1 | 1 | 3 | 12 | 0 | 235204 | 232732 | 10.12 |
| A | 3 | 3 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 3 | 38/42 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 6863 | 6973 | 10.44 |
| B | 3 | 96 | 6 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 16 | 0 | 1 | 5 | 37/42 | 0 | 0 | 0 | 0 | 3 | 1 | 1 | 0 | 2 | 0 | 235564 | 103280 | 6.05 |
| B+G | 3 | 96 | 6 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 3 | 16 | 0 | 0 | 5 | 34/42 | 0 | 0 | 0 | 0 | 3 | 1 | 1 | 0 | 2 | 0 | 235564 | 103280 | 6.05 |
| R | 3 | 94 | 18 | 0 | 0 | 0 | 1 | 17 | 0 | 0 | 0 | 0 | 6 | 14 | 1 | 2 | 40/42 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | 188347 | 136950 | 8.35 |
| R+G | 3 | 94 | 18 | 0 | 0 | 0 | 1 | 17 | 0 | 0 | 0 | 3 | 6 | 14 | 0 | 2 | 37/42 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | 188347 | 136950 | 8.35 |

### gold, hard

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 3 | 125 | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 81 | 5 | 20 | 0 | 38/39 | 0 | 0 | 0 | 0 | 17 | 3 | 3 | 6 | 8 | 0 | 287222 | 265861 | 11.31 |
| A-live+G | 3 | 125 | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 6 | 81 | 5 | 0 | 0 | 37/39 | 0 | 0 | 0 | 0 | 17 | 3 | 3 | 6 | 8 | 0 | 287222 | 265861 | 11.31 |
| A | 3 | 3 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 39/39 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 7513 | 8578 | 11.89 |
| B | 3 | 127 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 103 | 0 | 11 | 0 | 35/39 | 0 | 0 | 0 | 0 | 19 | 3 | 3 | 5 | 11 | 0 | 347873 | 179519 | 7.66 |
| B+G | 3 | 127 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 103 | 0 | 0 | 0 | 33/39 | 0 | 0 | 0 | 0 | 19 | 3 | 3 | 5 | 11 | 0 | 347873 | 179519 | 7.66 |
| R | 3 | 113 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 37 | 17 | 1 | 0 | 37/39 | 0 | 0 | 0 | 0 | 5 | 2 | 3 | 0 | 3 | 0 | 241175 | 214770 | 9.79 |
| R+G | 3 | 113 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 37 | 15 | 0 | 0 | 36/39 | 0 | 0 | 0 | 0 | 5 | 2 | 3 | 0 | 3 | 0 | 241175 | 214770 | 9.79 |

### gold, by ChatGPT

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-live | 4 | 152 | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 140 | 3 | 43 | 0 | 30/37 | 0 | 0 | 0 | 0 | 27 | 2 | 2 | 9 | 16 | 0 | 342431 | 288714 | 9.4 |
| A-live+G | 4 | 152 | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 4 | 140 | 3 | 0 | 0 | 30/37 | 0 | 0 | 0 | 0 | 27 | 2 | 2 | 9 | 16 | 0 | 342431 | 288714 | 9.4 |
| A | 4 | 4 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 37/37 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 9413 | 8211 | 11.89 |
| B | 4 | 148 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 180 | 0 | 24 | 1 | 34/37 | 0 | 0 | 0 | 0 | 23 | 2 | 2 | 7 | 14 | 0 | 380471 | 186615 | 7.01 |
| B+G | 4 | 148 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 4 | 180 | 0 | 0 | 1 | 34/37 | 0 | 0 | 0 | 0 | 23 | 2 | 2 | 7 | 14 | 0 | 380471 | 186615 | 7.01 |
| R | 4 | 127 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 21 | 5 | 1 | 1 | 36/37 | 0 | 0 | 0 | 0 | 2 | 2 | 2 | 0 | 0 | 0 | 260230 | 174807 | 7.25 |
| R+G | 4 | 127 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 6 | 21 | 5 | 0 | 1 | 36/37 | 0 | 0 | 0 | 0 | 2 | 2 | 2 | 0 | 0 | 0 | 260230 | 174807 | 7.25 |

gold: 24 errors on disputed labels, not counted above
  c04 run 1 A-live: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 A-live: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 A-live: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 A-live+G: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 A-live+G: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 A-live+G: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 B: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 B: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 B+G: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 B+G: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 R: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 R: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 R: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 R: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 R: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 R+G: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 R+G: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 R+G: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 R+G: work ['E2', 'clean_coil'] got declined, author's label deferred
  c04 run 1 R+G: work ['E2', 'clean_coil'] got declined, author's label deferred
  g01 run 1 A-live: work ['E1', 'replace_filter'] got proposed, author's label None
  g01 run 1 A-live+G: work ['E1', 'replace_filter'] got proposed, author's label None
  g01 run 1 R: work ['E1', 'replace_filter'] got proposed, author's label None
  g01 run 1 R+G: work ['E1', 'replace_filter'] got proposed, author's label None

gold: guards on A-live removed 0 live errors and added 0

gold: guards on B removed 0 live errors and added 0

gold: guards on R removed 0 live errors and added 0

### Headroom, gold

| visit | run | A-live | A-live+G | B | B+G | R | R+G |
|---|---|---|---|---|---|---|---|
| c01 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| c02 | 1 | 17 | 17 | 5 | 5 | 14 | 14 |
| c03 | 1 | 1 | 1 | 1 | 1 | 4 | 4 |
| c04 | 1 | 1 | 1 | 0 | 0 | 0 | 0 |
| g01 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| g02 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| g03 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| g04 | 1 | 1 | 1 | 0 | 0 | 0 | 0 |

Run 1: best simple arm B with 7: errors in 3 of 8 visits (c02, c03, g01), by type {'ordinary': 1, 'mixed': 6, 'hard': 0}, 27 questions of which 16 needless
Exploratory verdict (gold): NO HEADROOM: the best simple arm leaves too few AI-addressable errors in every run. Read it with the spread and the questions.
