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
        self._ensure_model_loaded()

        transcribe_kwargs = {
            "language": "en",
            "initial_prompt": self.domain_prompt,
            "beam_size": 1,
            "temperature": (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
            "condition_on_previous_text": False,
            "fp16": False,
        }

        try:
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


def word_error_rate(reference: str, hypothesis: str) -> float:
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()
    n, m = len(ref_words), len(hyp_words)

    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    if n == 0:
        return 0.0 if m == 0 else 100.0
    return 100.0 * dp[n][m] / n
