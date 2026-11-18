from types import SimpleNamespace

import fvr.asr as asr


class FakeWhisperModel:
    def __init__(self):
        self.calls = []

    def transcribe(self, path, **options):
        self.calls.append((path, options))
        words = [SimpleNamespace(word=" Head", probability=0.9), SimpleNamespace(word=" 312.", probability=0.4)]
        return iter([SimpleNamespace(text=" Head 312.", words=words)]), None


def test_other_systems_decode_with_faster_whisper(monkeypatch):
    model = FakeWhisperModel()
    monkeypatch.setattr(asr, "APPLE_SILICON", False)
    monkeypatch.setattr(asr, "_faster_model", lambda: model)
    d = asr.transcribe("line.wav", "HVAC service call.")
    assert (d.text, d.words) == ("Head 312.", [(" Head", 0.9), (" 312.", 0.4)])
    path, options = model.calls[0]
    assert path == "line.wav" and options["initial_prompt"] == "HVAC service call." and options["word_timestamps"]
    assert "temperature" not in options  # keep the fallback that retries a looping decode
