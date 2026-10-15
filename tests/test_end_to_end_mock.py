import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from src.step1_graph.graph_db import LocalQuoteGraph
from src.step1_graph.autocomplete import QuoteAutocompleter
from src.step2_voice.speaker_id import SpeakerIdentificationSystem
from src.step2_voice.asr import SpeechRecognizer
from src.step2_voice.tts import PersonalizedTTS
from src.step2_voice.chatbot import WhichQuoteChatbot
from src.api.server import app
from fastapi.testclient import TestClient


@pytest.fixture
def mock_pipeline_environment():
    """Sets up an isolated, end-to-end pipeline environment with mocked external dependencies."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Isolated Graph DB
        db_path = os.path.join(tmp_dir, "test_mock_graph.db")
        graph = LocalQuoteGraph(db_path=db_path)
        graph.insert_quote(
            quote="To be, or not to be, that is the question.",
            author="William Shakespeare",
            source="Hamlet, Act III",
            work="Hamlet",
            categories=["Drama", "Literature"]
        )
        graph.insert_quote(
            quote="Stay hungry, stay foolish.",
            author="Steve Jobs",
            source="Stanford Address",
            work="Speeches",
            categories=["Technology"]
        )
        autocompleter = QuoteAutocompleter(graph_db=graph)

        # 2. Speaker Identification system
        speaker_sys = SpeakerIdentificationSystem()
        speaker_sys.profiles_path = os.path.join(tmp_dir, "profiles.json")
        speaker_sys.embeddings_path = os.path.join(tmp_dir, "embeddings.npz")
        speaker_sys.profiles = {}
        speaker_sys.embeddings = {}

        # Register a mock user with deterministic embedding
        dim = 192
        dummy_embedding = np.ones(dim, dtype=np.float32) / np.sqrt(dim)
        speaker_sys.embeddings["Alice"] = dummy_embedding
        speaker_sys.profiles["Alice"] = {
            "name": "Alice",
            "voice_preference": {"voice": "en-US-JennyNeural", "rate": "+10%", "pitch": "+5Hz"},
            "sample_audio": "mock_sample.wav"
        }

        # 3. Mocked ASR module
        mock_asr = MagicMock(spec=SpeechRecognizer)
        mock_asr.transcribe.return_value = "Stay hungry"

        # 4. Mocked TTS module
        mock_tts = MagicMock(spec=PersonalizedTTS)
        dummy_audio_file = os.path.join(tmp_dir, "mock_tts_output.mp3")
        with open(dummy_audio_file, "wb") as f:
            f.write(b"MOCK_MP3_AUDIO_DATA")
        mock_tts.synthesize.return_value = dummy_audio_file

        # 5. Build WhichQuoteChatbot
        bot = WhichQuoteChatbot(
            autocompleter=autocompleter,
            speaker_system=speaker_sys,
            tts=mock_tts,
            asr=mock_asr
        )

        yield {
            "graph": graph,
            "autocompleter": autocompleter,
            "speaker_system": speaker_sys,
            "asr": mock_asr,
            "tts": mock_tts,
            "bot": bot,
            "tmp_dir": tmp_dir,
            "dummy_audio_file": dummy_audio_file
        }

        graph.close()


def test_full_voice_pipeline_flow(mock_pipeline_environment):
    """
    Tests complete voice pipeline:
    Audio In -> Speaker ID -> ASR Transcription -> Graph DB Quote Autocomplete -> Chatbot Reply -> Personalized TTS.
    """
    env = mock_pipeline_environment
    bot = env["bot"]
    speaker_sys = env["speaker_system"]

    # Mock speaker embedding extraction to match Alice
    with patch.object(speaker_sys, "extract_embedding") as mock_extract:
        mock_extract.return_value = speaker_sys.embeddings["Alice"]

        # Simulate voice turn with a dummy audio path
        dummy_input_audio = os.path.join(env["tmp_dir"], "input.wav")
        with open(dummy_input_audio, "wb") as f:
            f.write(b"RIFF_DUMMY_AUDIO")

        turn_result = bot.process_voice_turn(dummy_input_audio)

        # 1. Verify speaker recognition
        assert turn_result["speaker"] == "Alice"
        assert turn_result["confidence"] >= 0.99

        # 2. Verify ASR transcription
        assert turn_result["transcription"] == "Stay hungry"

        # 3. Verify graph autocomplete and source attribution
        assert "Steve Jobs" in turn_result["response"]
        assert "Stay hungry, stay foolish." in turn_result["response"]

        # 4. Verify personalized TTS invoked with Alice's custom settings
        env["tts"].synthesize.assert_called_once()
        call_args = env["tts"].synthesize.call_args
        passed_pref = call_args[1].get("voice_preference") or call_args[0][1]
        assert passed_pref["voice"] == "en-US-JennyNeural"
        assert passed_pref["rate"] == "+10%"
        assert passed_pref["pitch"] == "+5Hz"

        # 5. Verify audio response file generated
        assert turn_result["audio_response_path"] == env["dummy_audio_file"]
        assert os.path.exists(turn_result["audio_response_path"])


def test_unregistered_guest_voice_pipeline_flow(mock_pipeline_environment):
    """
    Tests that an unknown voice falls back cleanly to 'Guest' with default voice settings.
    """
    env = mock_pipeline_environment
    bot = env["bot"]
    speaker_sys = env["speaker_system"]

    # Mock speaker embedding extraction for a stranger (orthogonal vector -> cosine similarity 0)
    with patch.object(speaker_sys, "extract_embedding") as mock_extract:
        stranger_emb = np.zeros(192, dtype=np.float32)
        stranger_emb[0] = 1.0  # Orthogonal to Alice's uniform vector
        mock_extract.return_value = stranger_emb

        dummy_input_audio = os.path.join(env["tmp_dir"], "guest_input.wav")
        with open(dummy_input_audio, "wb") as f:
            f.write(b"GUEST_AUDIO")

        turn_result = bot.process_voice_turn(dummy_input_audio)

        assert turn_result["speaker"] == "Guest"
        assert "Steve Jobs" in turn_result["response"]


def test_conversational_attribution_intent(mock_pipeline_environment):
    """
    Tests the attribution intent ('Who said...') routing through the graph search.
    """
    env = mock_pipeline_environment
    bot = env["bot"]

    reply = bot.process_text_turn("Who said to be or not to be?", speaker_name="Alice")
    assert "William Shakespeare" in reply
    assert "Hamlet" in reply


def test_conversational_identity_intent(mock_pipeline_environment):
    """
    Tests the speaker identity query ('Who am I?').
    """
    env = mock_pipeline_environment
    bot = env["bot"]

    reply = bot.process_text_turn("Who am I?", speaker_name="Alice")
    assert "Alice" in reply


def test_fastapi_voice_turn_mock_endpoint():
    """
    Tests the FastAPI /api/step2/voice-turn HTTP endpoint end-to-end with mocked chatbot.
    """
    client = TestClient(app)

    mock_turn_result = {
        "speaker": "Alice",
        "confidence": 0.95,
        "transcription": "Stay hungry",
        "response": "I found the matching citation: 'Stay hungry, stay foolish.'. Source: Steve Jobs.",
        "audio_response_path": "/tmp/mock_audio.mp3",
        "voice_used": "en-US-JennyNeural"
    }

    # Create dummy temp file for audio response
    with open("/tmp/mock_audio.mp3", "wb") as f:
        f.write(b"MOCK_MP3_DATA")

    with patch("src.api.server.chatbot.process_voice_turn", return_value=mock_turn_result):
        # Send multipart audio file
        response = client.post(
            "/api/step2/voice-turn",
            files={"audio": ("sample.wav", b"FAKE_AUDIO_BYTES", "audio/wav")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["speaker"] == "Alice"
        assert data["transcription"] == "Stay hungry"
        assert "Steve Jobs" in data["response"]
        assert data["audio_url"] is not None
        assert data["audio_url"].startswith("/api/audio/")
