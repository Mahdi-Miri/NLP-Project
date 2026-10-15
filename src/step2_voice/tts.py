import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from config.settings import config
from src.utils.audio_utils import play_audio


class PersonalizedTTS:
    """
    Personalized Text-to-Speech synthesizer.
    Customizes pitch, speaking rate, and voice identity according to the recognized speaker's preferences.
    """

    def __init__(self, engine: Optional[str] = None):
        self.engine = engine or config.voice.tts_engine

    async def _synthesize_edge(self, text: str, output_path: str, voice: str, rate: str, pitch: str) -> str:
        """Asynchronously synthesizes speech using edge-tts neural voices."""
        import edge_tts
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
        await communicate.save(output_path)
        return output_path

    def _synthesize_pyttsx3(self, text: str, output_path: str, voice_id: Optional[str] = None, rate: int = 175) -> str:
        """Synthesizes speech using local offline pyttsx3 engine."""
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        if voice_id:
            try:
                engine.setProperty("voice", voice_id)
            except Exception:
                pass
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        return output_path

    def synthesize(
        self,
        text: str,
        voice_preference: Optional[Dict[str, Any]] = None,
        output_filepath: Optional[str] = None
    ) -> str:
        """
        Synthesizes text to an audio file configured with the speaker's voice preferences.
        """
        pref = voice_preference or config.voice.voice_presets.get("Default", {})
        voice_name = pref.get("voice", config.voice.default_voice)
        rate = pref.get("rate", "+0%")
        pitch = pref.get("pitch", "+0Hz")

        if not output_filepath:
            temp_dir = tempfile.gettempdir()
            output_filepath = os.path.join(temp_dir, f"tts_response_{os.getpid()}.mp3")

        if self.engine == "edge":
            try:
                asyncio.run(self._synthesize_edge(text, output_filepath, voice=voice_name, rate=rate, pitch=pitch))
                return output_filepath
            except Exception as e:
                print(f"[!] edge-tts failed ({e}). Falling back to pyttsx3 offline engine.")
                fallback_path = output_filepath.replace(".mp3", ".wav")
                return self._synthesize_pyttsx3(text, fallback_path)
        else:
            return self._synthesize_pyttsx3(text, output_filepath)

    def speak(self, text: str, voice_preference: Optional[Dict[str, Any]] = None) -> None:
        """
        Synthesizes and immediately plays the vocal response out loud.
        """
        audio_file = self.synthesize(text, voice_preference=voice_preference)
        play_audio(audio_file)
