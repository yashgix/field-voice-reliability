# VoiceCodeBench real-speech check (human recordings, codes and measurements)

| Condition | Noise | WER | Product codes exact | Broke vs none | Fixed vs none | Measurements exact | Unsaid record codes inserted | s/segment |
|---|---|---|---|---|---|---|---|---|
| none | clean | 8.0% | 80/90 | 0 | 0 | 27/28 | 0 | 3.6 |
| record | clean | 7.8% | 82/90 | 0 | 2 | 25/28 | 0 | 3.6 |
| wrong | clean | 7.8% | 81/90 | 0 | 1 | 25/28 | 0 | 3.6 |

Two-decode safeguard, record condition (accept a code only if both decodes agree):

- clean: 80 codes accepted correctly, 10 sent for confirmation (correct or not), 0 unsaid record codes accepted
