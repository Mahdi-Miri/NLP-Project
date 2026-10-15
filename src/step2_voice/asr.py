import os
from typing import Optional, Union
import numpy as np
import torch

from config.settings import config


class SpeechRecognizer:
    """
    Automatic Speech Recognition (ASR) module utilizing pre-trained Whisper models.
    Supports transcription from audio files and in-memory numpy buffers.
    """

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        self.model_name = model_name or config.voice.asr_model_name
        self.device = device or ("mps" if torch.backends.mps.is_available() else "cpu")
        self._model = None

    def _load_model(self):
        """Lazy-loads the Whisper model on first transcription request."""
        if self._model is None:
            import whisper
            print(f"[*] Loading pre-trained Whisper model '{self.model_name}' on device '{self.device}'...")
            self._model = whisper.load_model(self.model_name, device=self.device)
            print("[+] Whisper model loaded successfully.")

    def transcribe(self, audio_input: Union[str, np.ndarray]) -> str:
        """
        Transcribes speech audio into English text.
        Accepts either a filesystem path to an audio file (.wav/.mp3) or a float32 numpy array.
        """
        self._load_model()

        if isinstance(audio_input, (str, os.PathLike)):
            if not os.path.exists(audio_input):
                raise FileNotFoundError(f"Audio file not found: {audio_input}")
            # Load natively via soundfile to avoid external ffmpeg dependency
            from src.utils.audio_utils import load_audio
            audio_data, _ = load_audio(str(audio_input), target_sr=16000)
            if len(audio_data) == 0:
                return ""
            result = self._model.transcribe(audio_data.astype(np.float32), fp16=False)
        elif isinstance(audio_input, np.ndarray):
            # Whisper expects 16kHz float32 audio
            audio_data = audio_input.astype(np.float32)
            result = self._model.transcribe(audio_data, fp16=False)
        else:
            raise TypeError("audio_input must be either a file path string or numpy array.")

        transcription = result.get("text", "").strip()
        return transcription
