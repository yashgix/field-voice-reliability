"""Teacher-forced scoring with local Whisper (MLX).

Scoring answers "how well does the audio support this exact text?" with the decoder conditioned on nothing but
the audio. It is the acoustic check that separates a word the speaker said from one a context prompt pushed in.
"""

import mlx.core as mx
from mlx_whisper.audio import N_FRAMES, N_SAMPLES, load_audio, log_mel_spectrogram, pad_or_trim
from mlx_whisper.tokenizer import get_tokenizer
from mlx_whisper.transcribe import ModelHolder

from fvr.asr import MODEL


class Scorer:
    """Teacher-forced log-probability of candidate transcripts for one clip (audio encoded once)."""

    def __init__(self, audio_path: str):
        self.model = ModelHolder.get_model(MODEL, mx.float16)
        self.tokenizer = get_tokenizer(
            self.model.is_multilingual, num_languages=self.model.num_languages, language="en", task="transcribe"
        )
        audio = load_audio(audio_path)
        mel = log_mel_spectrogram(pad_or_trim(audio, N_SAMPLES), n_mels=self.model.dims.n_mels)
        mel = pad_or_trim(mel, N_FRAMES, axis=-2).astype(mx.float16)
        self.features = self.model.embed_audio(mel[None])

    def logprob(self, text: str) -> tuple[float, int]:
        """Total log-probability of `text` (plus end of text) and its token count, with no prompt."""
        prefix = list(self.tokenizer.sot_sequence_including_notimestamps)
        target = self.tokenizer.encode(" " + text.strip()) + [self.tokenizer.eot]
        tokens = mx.array([prefix + target[:-1]])
        logits = self.model.logits(tokens, self.features).astype(mx.float32)
        logp = logits - mx.logsumexp(logits, axis=-1, keepdims=True)
        picked = mx.take_along_axis(logp[0, len(prefix) - 1 :], mx.array(target)[:, None], axis=-1)
        return float(mx.sum(picked)), len(target)
