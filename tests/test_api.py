from fastapi.testclient import TestClient
import pytest

from main import app


@pytest.fixture
def client():
    """Create a test client for each test."""
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "languages" in payload


def test_languages_endpoint(client):
    response = client.get("/api/languages")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    codes = {item["code"] for item in payload}
    assert {"sat", "mun", "ho", "hi"}.issubset(codes)


def test_translation_endpoint_for_education_flow(client):
    response = client.post(
        "/api/translate",
        json={
            "source_text": "Two plus three equals five.",
            "source_language": "hi",
            "target_language": "mun",
            "domain": "mathematics",
            "mode": "education",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["target_language"] == "mun"
    assert payload["source_text"] == "Two plus three equals five."
    assert payload["translation"]
    assert payload["status"] in {"queued", "completed"}


def test_language_pack_summary_endpoint(client):
    response = client.get("/api/language-packs")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) >= 3
    first = payload[0]
    assert "code" in first
    assert "maturity" in first
    assert "glossary_count" in first
