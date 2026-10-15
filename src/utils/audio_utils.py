import os
import wave
from pathlib import Path
from typing import Optional, Tuple
import numpy as np


def record_audio(output_filepath: str, duration: float = 4.0, sample_rate: int = 16000) -> str:
    """
    Records audio from the default microphone and saves it as a 16kHz mono WAV file.
    """
    try:
        import sounddevice as sd
    except ImportError:
        raise RuntimeError("sounddevice is not installed. Please install it using pip.")

    print(f"[*] Recording for {duration} seconds... Speak now!")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
    sd.wait()
    print("[*] Recording complete.")

    os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
    with wave.open(output_filepath, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())

    return output_filepath


def load_audio(filepath: str, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
    """
    Loads an audio file as a mono float32 array normalized between -1.0 and 1.0.
    """
    try:
        import soundfile as sf
    except ImportError:
        raise RuntimeError("soundfile is not installed. Please install it using pip.")

    data, sr = sf.read(filepath, dtype="float32")

    # Convert to mono if multi-channel
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    # Simple resampling using scipy if sample rate differs
    if sr != target_sr:
        from scipy import signal
        num_samples = int(len(data) * target_sr / sr)
        data = signal.resample(data, num_samples)
        sr = target_sr

    return data, sr


def play_audio(filepath: str) -> None:
    """
    Plays an audio file through system speakers.
    """
    try:
        import sounddevice as sd
        import soundfile as sf
        data, fs = sf.read(filepath)
        sd.play(data, fs)
        sd.wait()
    except Exception as e:
        # Fallback to macOS afplay command if sounddevice playback fails
        if os.system(f"which afplay > /dev/null 2>&1") == 0:
            os.system(f"afplay '{filepath}'")
        else:
            print(f"[!] Warning: Audio playback failed: {e}")
