
### asr, all

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 1 | 1 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 16/19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2420 | 2994 | 13.98 |
| R | 1 | 45 | 1 | 2 | 0 | 2 | 1 | 0 | 0 | 0 | 1 | 5 | 69 | 6 | 1 | 0 | 21/27 | 3 | 0 | 3 | 0 | 8 | 1 | 2 | 2 | 5 | 0 | 110818 | 171363 | 16.78 |
| R+G | 1 | 45 | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 10 | 69 | 6 | 0 | 0 | 21/27 | 3 | 0 | 3 | 0 | 8 | 1 | 2 | 2 | 5 | 0 | 110818 | 171363 | 16.78 |

### asr, ordinary

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 1 | 1 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 16/19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2420 | 2994 | 13.98 |

### asr, hard

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R | 1 | 45 | 1 | 2 | 0 | 2 | 1 | 0 | 0 | 0 | 1 | 5 | 69 | 6 | 1 | 0 | 21/27 | 3 | 0 | 3 | 0 | 8 | 1 | 2 | 2 | 5 | 0 | 110818 | 171363 | 16.78 |
| R+G | 1 | 45 | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 10 | 69 | 6 | 0 | 0 | 21/27 | 3 | 0 | 3 | 0 | 8 | 1 | 2 | 2 | 5 | 0 | 110818 | 171363 | 16.78 |

asr: guards on R removed 1 live errors and added 0

### Headroom, asr

| visit | run | R | R+G |
|---|---|---|---|
| d02 | 1 | 1 | 1 |

Run 1: best simple arm R with 1: errors in 1 of 1 visits (d02), by type {'hard': 1}, 8 questions of which 5 needless
Exploratory verdict (asr): NO HEADROOM: the best simple arm leaves too few AI-addressable errors in every run. Read it with the spread and the questions.

### gold, all

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 1 | 1 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 19/19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2339 | 3188 | 14.66 |

### gold, ordinary

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 1 | 1 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 19/19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2339 | 3188 | 14.66 |

### Headroom, gold

| visit | run |  |
|---|---|
Exploratory verdict (gold): HEADROOM: the best simple arm leaves enough AI-addressable errors in every run. Read it with the spread and the questions.
