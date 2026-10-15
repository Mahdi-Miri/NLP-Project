import os
import tempfile
import pytest
import numpy as np

from src.utils.text_utils import clean_wiki_markup, normalize_query, extract_highlighted_match
from src.step1_graph.graph_db import LocalQuoteGraph
from src.step1_graph.autocomplete import QuoteAutocompleter
from src.step1_graph.parser import WikiquoteDumpParser
from src.step2_voice.speaker_id import SpeakerIdentificationSystem
from src.step2_voice.chatbot import WhichQuoteChatbot
from src.step2_voice.tts import PersonalizedTTS


def test_text_cleaning():
    raw = "'''Stay hungry''', [[stay foolish]] <!-- comment --> <ref>Stanford</ref>"
    cleaned = clean_wiki_markup(raw)
    assert cleaned == "Stay hungry, stay foolish"

    norm = normalize_query("To be, or not to be?!")
    assert norm == "to be or not to be"

    highlight = extract_highlighted_match("Stay hungry, stay foolish.", "Stay hungry")
    assert highlight["matched"] is True
    assert highlight["completion"] == ", stay foolish."


def test_graph_db_and_autocomplete():
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        graph = LocalQuoteGraph(db_path=tmp.name)

        # Test insertion
        qid = graph.insert_quote(
            quote="Imagination is more important than knowledge.",
            author="Albert Einstein",
            source="What Life Means to Einstein",
            work="Interviews",
            categories=["Physicists", "Science"]
        )
        assert qid > 0

        stats = graph.get_stats()
        assert stats["quotes"] == 1
        assert stats["authors"] == 1
        assert stats["works"] == 1

        # Test autocompletion
        ac = QuoteAutocompleter(graph_db=graph)
        results = ac.autocomplete("Imagination", top_k=1)
        assert len(results) == 1
        assert results[0]["author"] == "Albert Einstein"
        assert "knowledge" in results[0]["full_quote"]


def test_speaker_identification():
    with tempfile.TemporaryDirectory() as tmp_dir:
        speaker_sys = SpeakerIdentificationSystem()
        # Override paths for isolated testing
        speaker_sys.profiles_path = os.path.join(tmp_dir, "profiles.json")
        speaker_sys.embeddings_path = os.path.join(tmp_dir, "embeddings.npz")
        speaker_sys.profiles = {}
        speaker_sys.embeddings = {}

        # Synthesize dummy audio signals
        sr = 16000
        t = np.linspace(0, 1.0, sr)
        audio_user1 = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        audio_user2 = (0.5 * np.sin(2 * np.pi * 880 * t)).astype(np.float32)

        speaker_sys.register_user("Alice", audio_user1, {"voice": "en-US-JennyNeural"})

        # Identify user1
        name, sim, _ = speaker_sys.identify_speaker(audio_user1)
        assert name == "Alice"
        assert sim > 0.90


def test_chatbot_text_responses():
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        graph = LocalQuoteGraph(db_path=tmp.name)
        graph.insert_quote(
            quote="Stay hungry, stay foolish.",
            author="Steve Jobs",
            source="Stanford Address",
            work="Speeches",
            categories=["Tech"]
        )

        ac = QuoteAutocompleter(graph_db=graph)
        chatbot = WhichQuoteChatbot(autocompleter=ac)

        # Autocomplete turn
        resp = chatbot.process_text_turn("Stay hungry", speaker_name="Mahdi")
        assert "Steve Jobs" in resp
        assert "Stay hungry, stay foolish." in resp

        # Attribution turn
        attrib = chatbot.process_text_turn("Who said stay hungry?", speaker_name="Mahdi")
        assert "Steve Jobs" in attrib


def test_tts_synthesis():
    tts = PersonalizedTTS()
    with tempfile.NamedTemporaryFile(suffix=".mp3") as tmp:
        # Check synthesis without crashing
        out_path = tts.synthesize("Test quote completion.", output_filepath=tmp.name)
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0
