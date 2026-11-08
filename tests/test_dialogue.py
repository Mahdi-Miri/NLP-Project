import pytest
from src.dialogue.chatbot import NeapolitanArtChatbot


@pytest.fixture
def bot():
    return NeapolitanArtChatbot()


def test_single_turn_artwork_inquiry(bot):
    res = bot.process_utterance("Tell me about The Flagellation of Christ.")
    assert "Caravaggio" in res.system_response
    assert "Capodimonte" in res.system_response
    assert res.active_artwork == "The Flagellation of Christ"
    assert res.active_artist == "Caravaggio"


def test_multi_turn_coreference(bot):
    bot.process_utterance("Where can I find The Seven Works of Mercy?")
    res2 = bot.process_utterance("Who painted it?")
    assert "Caravaggio" in res2.system_response
    assert res2.active_artwork == "The Seven Works of Mercy"


def test_artist_listing(bot):
    res = bot.process_utterance("What works by Battistello can I see in Naples?")
    assert "The Liberation of Saint Peter" in res.system_response
    assert "The Washing of the Feet" in res.system_response
    assert res.active_artist == "Battistello Caracciolo"
