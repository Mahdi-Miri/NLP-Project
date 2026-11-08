import pytest
from src.data_pipeline.curated_dataset import NEAPOLITAN_ARTWORKS
from src.data_pipeline.graph_db import NeapolitanArtGraph
from src.data_pipeline.sparql_client import DBpediaSPARQLClient
from src.dialogue.inconsistency import InconsistencyDetector, InconsistencyType


@pytest.fixture(scope="module")
def graph_instance():
    client = DBpediaSPARQLClient()
    corpus = client.fetch_neapolitan_corpus()
    graph = NeapolitanArtGraph()
    graph.populate(corpus)
    return graph


@pytest.fixture(scope="module")
def detector(graph_instance):
    return InconsistencyDetector(graph_instance)


def test_artist_mismatch_detection(detector):
    report = detector.detect_inconsistencies("Did Battistello Caracciolo paint The Seven Works of Mercy?")
    assert report.is_inconsistent is True
    assert report.inconsistency_type == InconsistencyType.ARTIST_MISMATCH
    assert "Caravaggio" in report.suggested_correction


def test_location_mismatch_detection(detector):
    report = detector.detect_inconsistencies("Can I visit The Seven Works of Mercy at Capodimonte?")
    assert report.is_inconsistent is True
    assert report.inconsistency_type == InconsistencyType.LOCATION_MISMATCH
    assert "Pio Monte della Misericordia" in report.suggested_correction


def test_city_mismatch_detection(detector):
    report = detector.detect_inconsistencies("Where can I see The Calling of Saint Matthew in Naples?")
    assert report.is_inconsistent is True
    assert report.inconsistency_type == InconsistencyType.CITY_MISMATCH
    assert "Rome" in report.explanation


def test_out_of_scope_artist(detector):
    report = detector.detect_inconsistencies("Are there works by Leonardo da Vinci in this Naples tour?")
    assert report.is_inconsistent is True
    assert report.inconsistency_type == InconsistencyType.OUT_OF_SCOPE_ARTIST


def test_consistent_query_passes(detector):
    report = detector.detect_inconsistencies("Tell me about The Seven Works of Mercy at Pio Monte della Misericordia.")
    assert report.is_inconsistent is False
    assert report.inconsistency_type == InconsistencyType.NO_INCONSISTENCY


def test_michelangelo_merisi_is_not_flagged_as_out_of_scope(detector):
    report = detector.detect_inconsistencies(
        "Tell me about Michelangelo Merisi da Caravaggio's Seven Works of Mercy."
    )
    assert report.is_inconsistent is False


def test_which_painter_disambiguation_is_not_flagged(detector):
    report = detector.detect_inconsistencies(
        "Which painter, Caravaggio or Battistello, made the Seven Works of Mercy?"
    )
    assert report.is_inconsistent is False


def test_negated_wrong_artist_claim_is_correctly_flagged(detector):
    report = detector.detect_inconsistencies(
        "I think the Seven Works of Mercy is NOT by Caravaggio, right?"
    )
    assert report.is_inconsistent is True
    assert report.inconsistency_type == InconsistencyType.ARTIST_MISMATCH


def test_negated_correct_statement_is_not_flagged(detector):
    report = detector.detect_inconsistencies(
        "Caravaggio did not paint the Liberation of Saint Peter, correct?"
    )
    assert report.is_inconsistent is False


def test_negated_correct_statement_other_direction_is_not_flagged(detector):
    report = detector.detect_inconsistencies(
        "Battistello did not paint the Seven Works of Mercy, right?"
    )
    assert report.is_inconsistent is False


def test_negated_wrong_claim_about_true_artist_is_flagged(detector):
    report = detector.detect_inconsistencies(
        "The Liberation of Saint Peter was not painted by Battistello, right?"
    )
    assert report.is_inconsistent is True
    assert report.inconsistency_type == InconsistencyType.ARTIST_MISMATCH
