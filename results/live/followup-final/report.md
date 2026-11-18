
### asr+job-v2, all

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 8 | 8 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 12 | 9 | 51/105 | 15 | 3 | 10 | 2 | 59 | 0 | 4 | 0 | 39 | 8 | 12 | 0 | 23170 | 31675 | 17.8 |

### asr+job-v2, ordinary

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 2 | 2 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 3 | 1 | 15/24 | 8 | 2 | 5 | 1 | 12 | 0 | 0 | 0 | 10 | 1 | 1 | 0 | 5154 | 6253 | 16.15 |

### asr+job-v2, by Claude helper

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 4 | 4 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 5 | 6 | 35/68 | 9 | 2 | 6 | 1 | 36 | 0 | 2 | 0 | 28 | 2 | 6 | 0 | 11697 | 16982 | 18.91 |

### asr+job-v2, mixed

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 3 | 3 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 1 | 6 | 27/42 | 3 | 0 | 2 | 1 | 16 | 0 | 1 | 0 | 10 | 2 | 4 | 0 | 7984 | 11152 | 17.8 |

### asr+job-v2, hard

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 3 | 3 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 8 | 2 | 9/39 | 4 | 1 | 3 | 0 | 31 | 0 | 3 | 0 | 19 | 5 | 7 | 0 | 10032 | 14270 | 23.15 |

### asr+job-v2, by ChatGPT

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 4 | 4 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 7 | 3 | 16/37 | 6 | 1 | 4 | 1 | 23 | 0 | 2 | 0 | 11 | 6 | 6 | 0 | 11473 | 14693 | 16.52 |

asr+job-v2: 0 errors on disputed labels, not counted above

### Headroom, asr+job-v2

| visit | run |  |
|---|---|
Exploratory verdict (asr+job-v2): HEADROOM: the best simple arm leaves enough AI-addressable errors in every run. Read it with the spread and the questions.
