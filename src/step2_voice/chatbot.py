import random
from typing import Dict, Any, Optional, Tuple

from config.settings import config
from src.step1_graph.autocomplete import QuoteAutocompleter
from src.step1_graph.graph_db import get_quote_graph
from src.step2_voice.asr import SpeechRecognizer
from src.step2_voice.speaker_id import SpeakerIdentificationSystem
from src.step2_voice.tts import PersonalizedTTS
from src.utils.text_utils import clean_wiki_markup


class WhichQuoteChatbot:
    """
    Conversational agent coordinating voice interactions, speaker recognition,
    and quote discovery from the Wikiquote graph database.
    """

    def __init__(
        self,
        autocompleter: Optional[QuoteAutocompleter] = None,
        speaker_system: Optional[SpeakerIdentificationSystem] = None,
        tts: Optional[PersonalizedTTS] = None,
        asr: Optional[SpeechRecognizer] = None
    ):
        self.graph = get_quote_graph()
        self.autocompleter = autocompleter or QuoteAutocompleter(self.graph)
        self.speaker_system = speaker_system or SpeakerIdentificationSystem()
        self.tts = tts or PersonalizedTTS()
        self.asr = asr or SpeechRecognizer()

        # Quiz mode tracking
        self.active_quiz = None

    def process_voice_turn(self, audio_filepath: str) -> Dict[str, Any]:
        """
        End-to-end voice processing turn:
        1. Identifies the speaker from the audio sample.
        2. Transcribes voice command using ASR.
        3. Formulates conversational response.
        4. Synthesizes personalized audio output.
        """
        # Step 1: Speaker Recognition
        speaker_name, confidence, profile = self.speaker_system.identify_speaker(audio_filepath)

        # Step 2: Automatic Speech Recognition (ASR)
        transcribed_text = self.asr.transcribe(audio_filepath)

        # Step 3: Conversational response generation
        reply_text = self.process_text_turn(transcribed_text, speaker_name=speaker_name)

        # Step 4: Personalized Text-to-Speech (TTS)
        voice_pref = profile.get("voice_preference", config.voice.voice_presets.get("Default"))
        response_audio_path = self.tts.synthesize(reply_text, voice_preference=voice_pref)

        return {
            "speaker": speaker_name,
            "confidence": round(confidence, 3),
            "closest_match": profile.get("closest_match"),
            "closest_score": profile.get("closest_score"),
            "threshold": profile.get("threshold", config.voice.speaker_similarity_threshold),
            "transcription": transcribed_text,
            "response": reply_text,
            "audio_response_path": response_audio_path,
            "voice_used": voice_pref.get("voice")
        }

    def process_text_turn(self, user_input: str, speaker_name: str = "Guest") -> str:
        """
        Processes text command and returns a natural language response.
        """
        cleaned = clean_wiki_markup(user_input).strip()
        lowered = cleaned.lower()

        if not cleaned:
            return f"Hello {speaker_name}! I didn't catch that. You can ask me to autocomplete a quote or test your knowledge with 'quiz'."

        # Intent: Greetings & Identity
        if any(w in lowered for w in ["who am i", "identify me", "my name"]):
            return f"Based on your voice acoustic profile, you are identified as {speaker_name}."

        # Intent: Help
        if lowered in ["help", "what can you do", "commands"]:
            return (
                f"Welcome {speaker_name}! Here is what I can do:\n"
                "1. Autocomplete a quote: simply start saying a quote like 'Stay hungry' or 'To be or not to be'.\n"
                "2. Attribution: ask 'Who said darkness cannot drive out darkness?'\n"
                "3. Quiz game: type or say 'quiz' to test your quote knowledge!"
            )

        # Intent: Quiz answer evaluation
        if self.active_quiz and (len(cleaned.split()) <= 4 or "answer" in lowered):
            correct_author = self.active_quiz["author"].lower()
            quote_text = self.active_quiz["quote"]
            self.active_quiz = None

            if any(part in lowered for part in correct_author.split()):
                return f"Spot on, {speaker_name}! That quote was indeed said by {correct_author.title()}."
            else:
                return f"Good try {speaker_name}, but that was actually said by {correct_author.title()}! The full quote is: '{quote_text}'."

        # Intent: Start Quiz
        if "quiz" in lowered or "which quote" in lowered or "game" in lowered:
            return self._start_quiz(speaker_name)

        # Intent: Attribution query ("Who said...")
        if lowered.startswith("who said") or lowered.startswith("who wrote"):
            target_query = cleaned
            for prefix in ["who said", "who wrote", "who uttered", "who"]:
                if lowered.startswith(prefix):
                    target_query = cleaned[len(prefix):].strip(" ?:\"'")
                    break

            candidates = self.autocompleter.autocomplete(target_query, top_k=1)
            if candidates:
                match = candidates[0]
                return f"'{match['full_quote']}' was uttered by {match['author']} ({match['source']})."
            return f"I couldn't find a matching citation for that in the database, {speaker_name}."

        # Intent: Quote Autocompletion (Default NLP workflow)
        candidates = self.autocompleter.autocomplete(cleaned, top_k=2)
        if candidates:
            best = candidates[0]
            # Construct natural response indicating best-matching quote and source
            return (
                f"I found the matching citation: '{best['full_quote']}'. "
                f"Source: {best['author']} ({best['source']})."
            )

        return f"I could not match that sentence to any known quote in the graph, {speaker_name}. Try another phrase!"

    def _start_quiz(self, speaker_name: str) -> str:
        """Picks a random quote from the graph database for interactive quiz."""
        import sqlite3
        try:
            cursor = self.graph.conn.cursor()
            cursor.execute("""
                SELECT q.text, a.name AS author, q.source
                FROM quotes q
                JOIN edge_said_by es ON es.quote_id = q.id
                JOIN authors a ON a.id = es.author_id
                ORDER BY RANDOM() LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                self.active_quiz = {
                    "quote": row["text"],
                    "author": row["author"],
                    "source": row["source"]
                }
                return f"Quiz time, {speaker_name}! Who said this: '{row['text']}'?"
        except Exception:
            pass
        return "I need quotes loaded in the database first before starting the quiz!"
