import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import whisper
from src.speech.asr import DEFAULT_NEAPOLITAN_PROMPT, word_error_rate
from src.utils.audio_utils import load_and_normalize_audio

SAMPLES_DIR = PROJECT_ROOT / "data" / "accent_test_samples"
REFERENCES = json.loads((SAMPLES_DIR / "reference_sentences.json").read_text())

CONFIGS = {
    "baseline_small_t0_prompt": dict(model="small", temperature=0.0, beam_size=5, prompt=True),
    "medium_t0_prompt": dict(model="medium", temperature=0.0, beam_size=5, prompt=True),
    "medium_fallback_prompt": dict(model="medium", temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0), beam_size=5, prompt=True),
    "medium_fallback_noprompt": dict(model="medium", temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0), beam_size=5, prompt=False),
    "medium_fallback_beam1": dict(model="medium", temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0), beam_size=1, prompt=True),
    "medium_fallback_beam10": dict(model="medium", temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0), beam_size=10, prompt=True),
}

_model_cache = {}


def get_model(name):
    if name not in _model_cache:
        print(f"Loading whisper/{name} ...", flush=True)
        _model_cache[name] = whisper.load_model(name, device="cpu")
    return _model_cache[name]


results = {}
for cfg_name, cfg in CONFIGS.items():
    model = get_model(cfg["model"])
    kwargs = {
        "language": "en",
        "beam_size": cfg["beam_size"],
        "temperature": cfg["temperature"],
        "condition_on_previous_text": False,
        "fp16": False,
    }
    if cfg["prompt"]:
        kwargs["initial_prompt"] = DEFAULT_NEAPOLITAN_PROMPT

    total_wer = 0.0
    total_time = 0.0
    per_sentence = {}
    for sid, ref_text in REFERENCES.items():
        wav_path = SAMPLES_DIR / f"{sid}.wav"
        if not wav_path.exists():
            continue
        audio, _sr = load_and_normalize_audio(str(wav_path), target_sr=16000)
        t0 = time.time()
        out = model.transcribe(audio, **kwargs)
        elapsed = time.time() - t0
        hyp = out["text"].strip()
        wer = word_error_rate(ref_text, hyp)
        per_sentence[sid] = {"wer": round(wer, 1), "seconds": round(elapsed, 2), "hyp": hyp}
        total_wer += wer
        total_time += elapsed

    n = len(per_sentence)
    avg_wer = total_wer / n if n else None
    avg_time = total_time / n if n else None
    results[cfg_name] = {
        "avg_wer_percent": round(avg_wer, 1) if avg_wer is not None else None,
        "avg_seconds": round(avg_time, 2) if avg_time is not None else None,
        "per_sentence": per_sentence,
    }
    print(f"{cfg_name}: avg WER={avg_wer:.1f}%  avg time={avg_time:.2f}s", flush=True)

out_path = PROJECT_ROOT / "data" / "asr_hyperparam_tuning_results.json"
out_path.write_text(json.dumps(results, indent=2))
print(f"\nSaved to {out_path}")
