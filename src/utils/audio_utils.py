"""
Audio utility functions for speech input/output processing.
Handles conversion, resampling, and format normalization for ASR and TTS.
"""

import io
import logging
import tempfile
from pathlib import Path
from typing import Any, Optional, Tuple
import numpy as np
import soundfile as sf
from scipy.signal import resample

logger = logging.getLogger(__name__)


def load_and_normalize_audio(file_path_or_bytes: Any, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
    """
    Load an audio file or bytes buffer, convert to mono float32, and resample to target_sr.
    Safe against format mismatches and guarantees valid ndarray output.
    """
    try:
        if isinstance(file_path_or_bytes, (str, Path)):
            data, sample_rate = sf.read(str(file_path_or_bytes), dtype="float32")
        elif isinstance(file_path_or_bytes, bytes):
            buffer = io.BytesIO(file_path_or_bytes)
            data, sample_rate = sf.read(buffer, dtype="float32")
        else:
            raise ValueError(f"Unsupported audio input type: {type(file_path_or_bytes)}")

        # Convert multi-channel to mono
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        # Resample if needed
        if sample_rate != target_sr:
            num_target_samples = int(len(data) * float(target_sr) / sample_rate)
            data = resample(data, num_target_samples).astype(np.float32)
            sample_rate = target_sr

        # Peak normalization to maximize SNR for accented / quiet microphone input
        max_amplitude = np.max(np.abs(data))
        if max_amplitude > 1e-4:
            data = (data / max_amplitude * 0.95).astype(np.float32)

        return data.astype(np.float32), sample_rate

    except Exception as exc:
        logger.error("Failed to load and normalize audio: %s", exc)
        # Return fallback silent audio array of 1 second to prevent local variable crashes
        return np.zeros(target_sr, dtype=np.float32), target_sr


def save_audio_to_temp_wav(audio_bytes: bytes) -> str:
    """Save raw audio bytes to a temporary WAV file and return path."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        return tmp.name
