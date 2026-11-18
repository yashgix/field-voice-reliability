# COALA real-speech check (human read speech, manufacturing requests)

| Condition | Subset | WER | Rare-term misses | Fixed vs none | Broke vs none | Unsaid listed terms written | Term recall vs none (95% CI) |
|---|---|---|---|---|---|---|---|
| none | all | 7.0% | 101/254 | 0 | 0 | 0/253 | - |
| oracle | all | 5.4% | 57/254 | 44 | 0 | 0/253 | +17.3 pts [+13.1, +21.8] |
| wrong | all | 6.9% | 94/254 | 7 | 0 | 0/253 | +2.8 pts [+0.8, +5.1] |
| none | quiet | 6.8% | 42/124 | 0 | 0 | 0/120 | - |
| oracle | quiet | 5.3% | 24/124 | 18 | 0 | 0/120 | - |
| wrong | quiet | 6.9% | 42/124 | 0 | 0 | 0/120 | - |
| none | real_noise | 7.1% | 59/130 | 0 | 0 | 0/133 | - |
| oracle | real_noise | 5.6% | 33/130 | 26 | 0 | 0/133 | - |
| wrong | real_noise | 6.8% | 52/130 | 7 | 0 | 0/133 | - |

Every insertion of an unsaid listed term:

- none
