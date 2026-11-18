
### voice-v2, all

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 1 | 1 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 9/9 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 2588 | 3438 | 16.22 |
| B | 1 | 45 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 6 | 87 | 7 | 36 | 1 | 5/9 | 0 | 0 | 0 | 0 | 9 | 1 | 1 | 0 | 4 | 3 | 1 | 0 | 125757 | 83664 | 10.35 |
| B+G | 1 | 45 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 8 | 87 | 7 | 0 | 1 | 5/9 | 0 | 0 | 0 | 0 | 9 | 1 | 1 | 0 | 4 | 3 | 1 | 0 | 125757 | 83664 | 10.35 |

### voice-v2, hard

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 1 | 1 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 9/9 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 2588 | 3438 | 16.22 |
| B | 1 | 45 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 6 | 87 | 7 | 36 | 1 | 5/9 | 0 | 0 | 0 | 0 | 9 | 1 | 1 | 0 | 4 | 3 | 1 | 0 | 125757 | 83664 | 10.35 |
| B+G | 1 | 45 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 8 | 87 | 7 | 0 | 1 | 5/9 | 0 | 0 | 0 | 0 | 9 | 1 | 1 | 0 | 4 | 3 | 1 | 0 | 125757 | 83664 | 10.35 |

### voice-v2, by ChatGPT

| arm | visit_runs | decisions | live_ai_errors | live_asr_errors | live_asr_lost | live_asr_changed | live_missing_clarification | live_revision_status | live_reference | live_unsupported | live_unsafe_done | lag_points | hedge_points | dropped | off_schema | final_errors | completeness | asr_lost_values | recovered | asr_omitted | asr_corrupted | questions | answered | ambiguities | repeated | restated | cannot | needless | format_failures | input_tokens | output_tokens | median_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 1 | 1 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 9/9 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 2588 | 3438 | 16.22 |
| B | 1 | 45 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 6 | 87 | 7 | 36 | 1 | 5/9 | 0 | 0 | 0 | 0 | 9 | 1 | 1 | 0 | 4 | 3 | 1 | 0 | 125757 | 83664 | 10.35 |
| B+G | 1 | 45 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 8 | 87 | 7 | 0 | 1 | 5/9 | 0 | 0 | 0 | 0 | 9 | 1 | 1 | 0 | 4 | 3 | 1 | 0 | 125757 | 83664 | 10.35 |

voice-v2: 0 errors on disputed labels, not counted above

voice-v2: guards on B removed 0 live errors and added 0

### Headroom, voice-v2

| visit | run | B | B+G |
|---|---|---|---|
| g04 | 1 | 1 | 1 |

Run 1: best simple arm B with 1: errors in 1 of 1 visits (g04), by type {'hard': 1}, 9 questions of which 1 needless
Exploratory verdict (voice-v2): NO HEADROOM: the best simple arm leaves too few AI-addressable errors in every run. Read it with the spread and the questions.
