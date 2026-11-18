# Browser capture check (headless Chrome on this Mac, synthetic voice as the microphone)

Said: "Line voltage is two forty one volts." (macOS `say`, Chrome's fake microphone), by `scripts/mvp_browser_check.py`.

- Clip received: 48000 Hz, 1 channel, 16-bit PCM WAV, 4.7 s
- Whisper heard: "Line voltage is 241V." (clip problem: None)
- Stored: Line voltage = 241 volts (accepted, checker)
- Next prompt: "L1 current."
- Audit: {'events': 3, 'chain_problems': [], 'clips_missing_or_changed': [], 'untraceable_values': []}
