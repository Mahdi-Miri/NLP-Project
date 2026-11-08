import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional

from config.settings import config

logger = logging.getLogger(__name__)

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    edge_tts = None

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    pyttsx3 = None


class TextToSpeechSynthesizer:
    def __init__(
        self,
        voice: Optional[str] = None,
        engine: Optional[str] = None,
    ):
        self.voice = voice or config.speech.tts_voice
        self.preferred_engine = engine or config.speech.tts_engine

    def synthesize_to_file(self, text: str, output_filepath: Optional[str] = None) -> str:
        clean_text = self._sanitize_text(text)
        if not clean_text:
            clean_text = "No content to read."

        if not output_filepath:
            suffix = ".mp3" if self.preferred_engine == "edge" else ".wav"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                output_filepath = tmp.name

        if self.preferred_engine == "edge" and EDGE_TTS_AVAILABLE:
            try:
                self._run_edge_tts(clean_text, output_filepath)
                return output_filepath
            except Exception as exc:
                logger.warning("Edge-TTS synthesis failed (%s), falling back to pyttsx3...", exc)

        if PYTTSX3_AVAILABLE:
            try:
                self._run_pyttsx3(clean_text, output_filepath)
                return output_filepath
            except Exception as exc:
                logger.error("pyttsx3 synthesis failed: %s", exc)

        logger.error("No TTS engine was able to synthesize audio.")
        return output_filepath

    def synthesize_to_bytes(self, text: str) -> bytes:
        filepath = self.synthesize_to_file(text)
        try:
            with open(filepath, "rb") as f:
                return f.read()
        except Exception as exc:
            logger.error("Failed to read synthesized audio file: %s", exc)
            return b""

    def _sanitize_text(self, text: str) -> str:
        cleaned = text.replace("*", "").replace("#", "").replace("`", "")
        cleaned = cleaned.replace("Notice:", "Notice.").replace("Clarification:", "Clarification.")
        return cleaned.strip()

    def _run_edge_tts(self, text: str, output_path: str):
        async def _speak():
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_path)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                loop.run_until_complete(_speak())
            else:
                loop.run_until_complete(_speak())
        except RuntimeError:
            asyncio.run(_speak())

    def _run_pyttsx3(self, text: str, output_path: str):
        engine = pyttsx3.init()
        engine.setProperty("rate", 160)
        engine.save_to_file(text, output_path)
        engine.runAndWait()
