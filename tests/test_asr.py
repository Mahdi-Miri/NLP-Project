from pathlib import Path

from src.speech.asr import SpeechRecognizer, word_error_rate

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_AUDIO = PROJECT_ROOT / "data" / "test_voice_turn.mp3"


def test_word_error_rate_matches_textbook_example():
    reference = "i UM the PHONE IS i LEFT THE portable PHONE UPSTAIRS last night"
    hypothesis = "i GOT IT TO the FULLEST i LOVE TO portable FORM OF STORES last night"
    wer = word_error_rate(reference, hypothesis)
    assert abs(wer - 76.9) < 1.0


def test_word_error_rate_identical_strings_is_zero():
    assert word_error_rate("tell me about the seven works of mercy", "tell me about the seven works of mercy") == 0.0


def test_asr_transcription_word_error_rate_on_sample_clip():
    reference = "Tell me about the Seven Works of Mercy by Caravaggio in Pio Monte della Misericordia."
    recognizer = SpeechRecognizer()
    hypothesis, _ = recognizer.transcribe(str(SAMPLE_AUDIO))
    wer = word_error_rate(reference, hypothesis)
    assert wer <= 10.0, f"WER too high: {wer:.1f}% (hypothesis: {hypothesis!r})"
