"""
Automatic Speech Recognition (ASR) module using OpenAI Whisper.
Transcribes user voice questions with robust error handling and format normalization.
"""

import logging
from pathlib import Path
from typing import Any, Optional, Tuple, Union
import numpy as np

from config.settings import config
from src.utils.audio_utils import load_and_normalize_audio

logger = logging.getLogger(__name__)

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None


DEFAULT_NEAPOLITAN_PROMPT = (
    "Scholarly inquiries on Caravaggio (Michelangelo Merisi) and Battistello Caracciolo in Naples, Italy. "
    "Masterpieces: The Seven Works of Mercy, The Flagellation of Christ, The Martyrdom of Saint Ursula, "
    "The Liberation of Saint Peter, The Washing of the Feet, Christ at the Column, Trinitas Terrestris, "
    "Frescoes of the Chapel of the Assunta. "
    "Venues: Pio Monte della Misericordia, Museo Nazionale di Capodimonte, "
    "Gallerie d'Italia Palazzo Zevallos Stigliano, Certosa di San Martino, Chiesa della Pietà dei Turchini. "
    "Baroque, chiaroscuro, tenebrism, art history in Naples."
)


class SpeechRecognizer:
    """
    ASR wrapper around OpenAI Whisper for speech-to-text with domain context conditioning.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        domain_prompt: Optional[str] = None,
    ):
        self.model_name = model_name or config.speech.asr_model_name
        self.device = device or config.speech.asr_device
        self.domain_prompt = domain_prompt or DEFAULT_NEAPOLITAN_PROMPT
        self._model = None

    def _ensure_model_loaded(self):
        if self._model is None:
            if not WHISPER_AVAILABLE:
                raise RuntimeError("Whisper is not installed. Please install 'openai-whisper'.")
            logger.info("Loading Whisper model '%s' on %s...", self.model_name, self.device)
            self._model = whisper.load_model(self.model_name, device=self.device)

    def transcribe(self, audio_source: Union[str, Path, bytes, np.ndarray]) -> Tuple[str, str]:
        """
        Transcribe audio input to text with domain prompting and forced English decoding.
        Returns:
            Tuple[str, str]: (transcribed_text, detected_language)
        """
        self._ensure_model_loaded()

        transcribe_kwargs = {
            "language": "en",
            "initial_prompt": self.domain_prompt,
            "beam_size": 5,
            "temperature": 0.0,
            "condition_on_previous_text": False,
            "fp16": False,
        }

        try:
            # Decode any input format (str path, Path, bytes, or ndarray) to normalized 16kHz float32
            if isinstance(audio_source, np.ndarray):
                audio_array = audio_source.astype(np.float32)
            else:
                audio_array, _ = load_and_normalize_audio(audio_source, target_sr=16000)

            if len(audio_array) == 0:
                return "", "en"

            result = self._model.transcribe(audio_array, **transcribe_kwargs)
            text = result.get("text", "").strip()
            lang = result.get("language", "en")
            return text, lang

        except Exception as exc:
            logger.error("ASR transcription error: %s", exc)
            return "", "en"
