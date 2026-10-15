from fastapi.testclient import TestClient
from src.api.server import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_stats_endpoint():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert "quotes" in data["stats"]


def test_autocomplete_endpoint():
    response = client.post("/api/step1/autocomplete", json={"query": "To be", "top_k": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert "Shakespeare" in data["results"][0]["author"]


def test_text_turn_endpoint():
    response = client.post("/api/step2/text-turn", json={"text": "Stay hungry", "speaker": "Mahdi"})
    assert response.status_code == 200
    data = response.json()
    assert "Steve Jobs" in data["response"]
