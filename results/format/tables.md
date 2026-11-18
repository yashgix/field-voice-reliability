# Format-priming comparison (synthetic, utterances with a spoken model number)

## test: 49 utterances x 4 noise conditions, 196 model numbers

| Context | clean | ac_5 | ac_0 | babble_5 | All | vs none (95% CI) | Unsaid prompt model numbers written |
|---|---|---|---|---|---|---|---|
| none | 78% | 67% | 53% | 63% | 65.3% (128/196) | - | - |
| brand | 78% | 67% | 57% | 59% | 65.3% (128/196) | +0.0 [-3.1, +3.1] | - |
| pattern | 78% | 76% | 71% | 63% | 71.9% (141/196) | +6.6 [+0.0, +13.8] | 0 |
| stale | 98% | 92% | 92% | 84% | 91.3% (179/196) | +26.0 [+14.8, +38.3] | 0 |
| job | 100% | 96% | 96% | 96% | 96.9% (190/196) | +31.6 [+21.4, +43.9] | 0 |

## dev: 15 utterances x 4 noise conditions, 60 model numbers

| Context | clean | ac_5 | ac_0 | babble_5 | All | vs none (95% CI) | Unsaid prompt model numbers written |
|---|---|---|---|---|---|---|---|
| none | 87% | 80% | 73% | 67% | 76.7% (46/60) | - | - |
| brand | 87% | 80% | 80% | 67% | 78.3% (47/60) | +1.7 [+0.0, +5.0] | - |
| pattern | 93% | 93% | 87% | 73% | 86.7% (52/60) | +10.0 [+0.0, +23.3] | 0 |
| stale | 93% | 100% | 100% | 93% | 96.7% (58/60) | +20.0 [+5.0, +40.0] | 0 |
| job | 100% | 100% | 100% | 100% | 100.0% (60/60) | +23.3 [+6.7, +45.0] | 0 |

