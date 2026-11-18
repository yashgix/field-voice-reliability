# Data, models and provenance

Models, datasets and rendered audio live in `~/field-voice-data/` (outside git). This repository holds the generated
text manifests and results, and the demo audio listed at the end. Downloaded 15 Nov 2026.

| Item | Source | License | What is used | Size |
|---|---|---|---|---|
| Whisper large-v3-turbo (MLX) | [mlx-community/whisper-large-v3-turbo](https://huggingface.co/mlx-community/whisper-large-v3-turbo), revision `a4aaeec0636e6fef84abdcbe3544cb2bf7e9f6fb` | MIT (OpenAI Whisper weights) | All decoding and scoring | 1.6 GB |
| VoiceCodeBench | [besimple-ai/voice-code-bench](https://huggingface.co/datasets/besimple-ai/voice-code-bench), revision `8edfa398aa5575816d940793e4e2b8c6430184da`; paper [arXiv 2608.28916](https://arxiv.org/abs/2608.28916) | Non-audio files MIT (Copyright the VoiceCodeBench authors; reference transcripts appear in `results/vcb/`). Audio: use, copy, modify and distribute allowed; **no voice cloning**; license notice must travel with any copy | 94 of 300 human-recorded segments: those with a `product_code` or `measurement` entity (`subset.txt`), 59 speakers | 0.6 GB |
| MS-SNSD noise | [microsoft/MS-SNSD](https://github.com/microsoft/MS-SNSD) | Code MIT; noise clips from Freesound selected as CC0 (README "Dataset licenses") | `AirConditioner`, `Babble` (and `NeighborSpeaking`, `VacuumCleaner`, `WasherDryer` downloaded, unused). `noise_train` for dev, `noise_test` for test | 0.16 GB |
| COALA voice data | [Zenodo 8268928](https://zenodo.org/records/8268928) | CC0 1.0 | English read speech from manufacturing scripts, crowd speakers with consent (see the record) | 1.8 GB |
| Synthetic utterances | Generated here (`fvr/synth.py`, seed in `configs/pilot.json`) with macOS `say` voices | Scripts ours; the voices are Apple's macOS system voices | 24 invented jobs, 108 utterances. Brand names are real; model-number strings are invented in the brands' styles | small |

Total downloaded: about 4.5 GB (model 1.6, COALA 1.8, VoiceCodeBench 0.6, noise 0.16, Python packages about 0.35).

**Demo audio** (`demo/audio/live/`, served with the replay page): visit lines voiced with macOS `say` voices, some
mixed with MS-SNSD babble noise (CC0), and one visit read aloud by the author, who agreed to its publication.

Rules followed: readings never appear in any context prompt; equipment and product codes appear only where a real
record would hold them; every job record and context string is generated and frozen before decoding (it is stored
in each manifest row next to the audio path); noise slices and files are chosen by seed and recorded per row.
