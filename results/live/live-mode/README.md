# Live mode runs

One visit (g04, four units, 36 lines) read aloud by one person in three takes (quiet room, music playing, an air duster
going off), played into the live-mode server line by line at speaking pace by `live/feed.py`. These are replays of one
recording, not separate live sessions. Nobody answers the questions in a replay. Latency is measured from when the
server receives a line; add the page's 0.7 s pause for the time after the speaker stops.

| Run | Setup | Facts | Wrong entries | Median latency | Cost |
|---|---|---|---|---|---|
| 1 | first version (the same question could be reworded and asked again) | 6 of 9 | 2 | 2.73 s | $0.0159 |
| 2 | one question per reading and unit | 6 of 9 | 3 | 2.65 s | $0.0142 |
| 3 | same as 2 | 6 of 9 | 0 | 2.60 s | $0.0138 |
| 4 | first wording of the spoken-number note, dropped because it made the model doubt ordinary decimals | 5 of 9 | 2 | 2.75 s | $0.0149 |
| 5 | final: questions only about unsettled readings, installed replacement = done, numbers read by what makes sense | 6 of 9 | 1 | 2.93 s | $0.0155 |
| 6 | same as 5 | 6 of 9 | 1 | 2.97 s | $0.0159 |

`mic-session1.json` to `mic-session3.json` are live microphone sessions on a laptop with a short 10-line script. Session
1 lost a soft line (the room level was measured once while the microphone was adjusting its gain). In session 2 the
page heard its own spoken questions. Both were fixed before session 3, which had neither problem.
