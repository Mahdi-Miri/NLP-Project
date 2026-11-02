"""
Unit tests for the Inconsistency Detection Engine.
Validates detection of attribution errors, venue mismatches, and city contradictions.
"""

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
    # Falsely claiming Battistello painted The Seven Works of Mercy
    report = detector.detect_inconsistencies("Did Battistello Caracciolo paint The Seven Works of Mercy?")
    assert report.is_inconsistent is True
    assert report.inconsistency_type == InconsistencyType.ARTIST_MISMATCH
    assert "Caravaggio" in report.suggested_correction


def test_location_mismatch_detection(detector):
    # Falsely claiming The Seven Works of Mercy is at Capodimonte
    report = detector.detect_inconsistencies("Can I visit The Seven Works of Mercy at Capodimonte?")
    assert report.is_inconsistent is True
    assert report.inconsistency_type == InconsistencyType.LOCATION_MISMATCH
    assert "Pio Monte della Misericordia" in report.suggested_correction


def test_city_mismatch_detection(detector):
    # Inquiring about a Roman artwork in Naples
    report = detector.detect_inconsistencies("Where can I see The Calling of Saint Matthew in Naples?")
    assert report.is_inconsistent is True
    assert report.inconsistency_type == InconsistencyType.CITY_MISMATCH
    assert "Rome" in report.explanation


def test_out_of_scope_artist(detector):
    # Asking about Leonardo da Vinci
    report = detector.detect_inconsistencies("Are there works by Leonardo da Vinci in this Naples tour?")
    assert report.is_inconsistent is True
    assert report.inconsistency_type == InconsistencyType.OUT_OF_SCOPE_ARTIST


def test_consistent_query_passes(detector):
    # Correct factual question
    report = detector.detect_inconsistencies("Tell me about The Seven Works of Mercy at Pio Monte della Misericordia.")
    assert report.is_inconsistent is False
    assert report.inconsistency_type == InconsistencyType.NO_INCONSISTENCY
