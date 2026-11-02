"""
Unified Speech Chatbot pipeline for Neapolitan Artistic Heritage.
Integrates Whisper ASR, Graph-Grounded Dialogue Management, and TTS output.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np
from pydantic import BaseModel

from src.dialogue.chatbot import NeapolitanArtChatbot
from src.dialogue.inconsistency import InconsistencyReport
from src.speech.asr import SpeechRecognizer
from src.speech.tts import TextToSpeechSynthesizer

logger = logging.getLogger(__name__)


class SpeechTurnResult(BaseModel):
    user_utterance: str
    detected_language: str
    system_response: str
    response_audio_path: Optional[str] = None
    inconsistency_report: InconsistencyReport
    active_artist: Optional[str] = None
    active_artwork: Optional[str] = None
    active_location: Optional[str] = None


class NeapolitanSpeechChatbot:
    """
    End-to-end multimodal speech chatbot supporting voice input,
    graph reasoning with contradiction detection, and spoken responses.
    """

    def __init__(
        self,
        chatbot: Optional[NeapolitanArtChatbot] = None,
        asr: Optional[SpeechRecognizer] = None,
        tts: Optional[TextToSpeechSynthesizer] = None,
    ):
        self.chatbot = chatbot or NeapolitanArtChatbot()
        self.asr = asr or SpeechRecognizer()
        self.tts = tts or TextToSpeechSynthesizer()

    def process_voice_turn(
        self, audio_source: Union[str, Path, bytes, np.ndarray], generate_speech: bool = True
    ) -> SpeechTurnResult:
        """
        Process speech input: transcribe -> query dialogue engine -> synthesize speech output.
        """
        # Step 1: Speech-to-Text
        transcript, language = self.asr.transcribe(audio_source)
        if not transcript.strip():
            fallback_text = "I could not hear or transcribe any voice input. Please try speaking again."
            audio_path = self.tts.synthesize_to_file(fallback_text) if generate_speech else None
            return SpeechTurnResult(
                user_utterance="",
                detected_language=language,
                system_response=fallback_text,
                response_audio_path=audio_path,
                inconsistency_report=InconsistencyReport(is_inconsistent=False),
            )

        # Step 2: Dialogue & Inconsistency Reasoning
        dialogue_result = self.chatbot.process_utterance(transcript)

        # Step 3: Text-to-Speech
        audio_path = None
        if generate_speech:
            audio_path = self.tts.synthesize_to_file(dialogue_result.system_response)

        return SpeechTurnResult(
            user_utterance=dialogue_result.user_utterance,
            detected_language=language,
            system_response=dialogue_result.system_response,
            response_audio_path=audio_path,
            inconsistency_report=dialogue_result.inconsistency_report,
            active_artist=dialogue_result.active_artist,
            active_artwork=dialogue_result.active_artwork,
            active_location=dialogue_result.active_location,
        )

    def process_text_turn(
        self, text_input: str, generate_speech: bool = True
    ) -> SpeechTurnResult:
        """
        Process text input with optional voice output synthesis.
        """
        dialogue_result = self.chatbot.process_utterance(text_input)
        audio_path = None
        if generate_speech:
            audio_path = self.tts.synthesize_to_file(dialogue_result.system_response)

        return SpeechTurnResult(
            user_utterance=dialogue_result.user_utterance,
            detected_language="en",
            system_response=dialogue_result.system_response,
            response_audio_path=audio_path,
            inconsistency_report=dialogue_result.inconsistency_report,
            active_artist=dialogue_result.active_artist,
            active_artwork=dialogue_result.active_artwork,
            active_location=dialogue_result.active_location,
        )

    def reset(self):
        """Reset conversation context."""
        self.chatbot.reset_dialogue()
