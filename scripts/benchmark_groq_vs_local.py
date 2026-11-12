import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import whisper
from groq import Groq

from src.speech.asr import DEFAULT_NEAPOLITAN_PROMPT, word_error_rate
from src.utils.audio_utils import load_and_normalize_audio

SAMPLES_DIR = PROJECT_ROOT / "data" / "accent_test_samples"
REFERENCES = json.loads((SAMPLES_DIR / "reference_sentences.json").read_text())

GROQ_MODELS = ["whisper-large-v3-turbo", "whisper-large-v3"]


def run_local_whisper():
    print("Loading local Whisper (medium)...", flush=True)
    model = whisper.load_model("medium", device="cpu")
    kwargs = {
        "language": "en",
        "initial_prompt": DEFAULT_NEAPOLITAN_PROMPT,
        "beam_size": 1,
        "temperature": (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
        "condition_on_previous_text": False,
        "fp16": False,
    }
    per_sentence = {}
    total_wer, total_time = 0.0, 0.0
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
        print(f"  {sid}: wer={wer:.1f}% time={elapsed:.2f}s -> {hyp}", flush=True)
    n = len(per_sentence)
    return {
        "avg_wer_percent": round(total_wer / n, 1) if n else None,
        "avg_seconds": round(total_time / n, 2) if n else None,
        "per_sentence": per_sentence,
    }


def run_groq(model_name: str):
    print(f"Running Groq ({model_name})...", flush=True)
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    per_sentence = {}
    total_wer, total_time = 0.0, 0.0
    for sid, ref_text in REFERENCES.items():
        wav_path = SAMPLES_DIR / f"{sid}.wav"
        if not wav_path.exists():
            continue
        with open(wav_path, "rb") as f:
            audio_bytes = f.read()
        t0 = time.time()
        resp = client.audio.transcriptions.create(
            file=(f"{sid}.wav", audio_bytes),
            model=model_name,
            language="en",
            prompt=DEFAULT_NEAPOLITAN_PROMPT,
            temperature=0.0,
        )
        elapsed = time.time() - t0
        hyp = resp.text.strip()
        wer = word_error_rate(ref_text, hyp)
        per_sentence[sid] = {"wer": round(wer, 1), "seconds": round(elapsed, 2), "hyp": hyp}
        total_wer += wer
        total_time += elapsed
        print(f"  {sid}: wer={wer:.1f}% time={elapsed:.2f}s -> {hyp}", flush=True)
    n = len(per_sentence)
    return {
        "avg_wer_percent": round(total_wer / n, 1) if n else None,
        "avg_seconds": round(total_time / n, 2) if n else None,
        "per_sentence": per_sentence,
    }


def main():
    results = {}
    try:
        results["local_whisper_medium"] = run_local_whisper()
    except Exception as exc:
        print(f"Local Whisper failed: {exc}", flush=True)
        results["local_whisper_medium"] = {"error": str(exc)}
    for model_name in GROQ_MODELS:
        try:
            results[f"groq_{model_name}"] = run_groq(model_name)
        except Exception as exc:
            print(f"Groq model {model_name} failed: {exc}", flush=True)
            results[f"groq_{model_name}"] = {"error": str(exc)}

    out_path = PROJECT_ROOT / "data" / "asr_groq_vs_local_benchmark.json"
    out_path.write_text(json.dumps(results, indent=2))

    print("\n=== Summary ===")
    for name, r in results.items():
        if "error" in r:
            print(f"{name}: FAILED ({r['error']})")
        else:
            print(f"{name}: avg WER={r['avg_wer_percent']}%  avg time={r['avg_seconds']}s")
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
