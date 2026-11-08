import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.speech.asr import word_error_rate
from src.utils.audio_utils import load_and_normalize_audio

SAMPLE_AUDIO = PROJECT_ROOT / "data" / "test_voice_turn.mp3"
REFERENCE = "Tell me about the Seven Works of Mercy by Caravaggio in Pio Monte della Misericordia."
INITIAL_PROMPT = (
    "Caravaggio, Battistello Caracciolo, Pio Monte della Misericordia, "
    "Seven Works of Mercy, Naples, Capodimonte"
)

results = []


def run_openai_whisper(size: str):
    import whisper

    model = whisper.load_model(size, device="cpu")
    audio, _sr = load_and_normalize_audio(str(SAMPLE_AUDIO))
    t0 = time.time()
    out = model.transcribe(audio, language="en", temperature=0.0, initial_prompt=INITIAL_PROMPT)
    elapsed = time.time() - t0
    hyp = out["text"].strip()
    return hyp, elapsed


def run_faster_whisper(size: str, compute_type: str = "int8"):
    from faster_whisper import WhisperModel

    model = WhisperModel(size, device="cpu", compute_type=compute_type)
    t0 = time.time()
    segments, _ = model.transcribe(str(SAMPLE_AUDIO), language="en", initial_prompt=INITIAL_PROMPT)
    hyp = " ".join(seg.text.strip() for seg in segments)
    elapsed = time.time() - t0
    return hyp, elapsed


configs = [
    ("openai-whisper", "tiny", run_openai_whisper, ("tiny",)),
    ("openai-whisper", "base", run_openai_whisper, ("base",)),
    ("openai-whisper", "small", run_openai_whisper, ("small",)),
    ("openai-whisper", "medium", run_openai_whisper, ("medium",)),
    ("faster-whisper", "small", run_faster_whisper, ("small",)),
    ("faster-whisper", "medium", run_faster_whisper, ("medium",)),
]

for backend, size, fn, args in configs:
    label = f"{backend}/{size}"
    print(f"Running {label} ...", flush=True)
    try:
        hyp, elapsed = fn(*args)
        wer = word_error_rate(REFERENCE, hyp)
        print(f"  done in {elapsed:.1f}s  WER={wer:.1f}%  hyp={hyp!r}")
        results.append({
            "backend": backend,
            "size": size,
            "seconds": round(elapsed, 2),
            "wer_percent": round(wer, 1),
            "hypothesis": hyp,
        })
    except Exception as e:
        print(f"  FAILED: {e}")
        results.append({"backend": backend, "size": size, "error": str(e)})

out_path = PROJECT_ROOT / "data" / "asr_benchmark_results.json"
out_path.write_text(json.dumps(results, indent=2))
print(f"\nSaved results to {out_path}")
