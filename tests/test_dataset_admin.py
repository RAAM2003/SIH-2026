import pytest

from main import app


def test_dataset_entry_submission_and_listing(client):
    payload = {
        "source_language": "hi",
        "target_language": "sat",
        "domain": "mathematics",
        "source_text": "दो और तीन का योग क्या है?",
        "target_text": "ᱟᱨᱡᱚᱜ ᱟᱨ ᱛᱤᱱᱤ ᱠᱚ ᱫᱟᱨ ᱠᱟᱱᱟ?",
        "validated": True,
    }

    create_response = client.post("/api/dataset/entries", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["source_language"] == "hi"
    assert created["target_language"] == "sat"

    list_response = client.get("/api/dataset/entries")
    assert list_response.status_code == 200
    entries = list_response.json()
    assert isinstance(entries, list)
    assert len(entries) >= 1
    assert any(item["source_language"] == "hi" and item["target_language"] == "sat" for item in entries)


def test_dataset_stats_endpoint(client):
    # First, create an entry so stats has data
    payload = {
        "source_language": "sat",
        "target_language": "mun",
        "domain": "fln",
        "source_text": "ᱟᱨᱡᱚᱜ",
        "target_text": "Khabar",
        "validated": True,
    }
    client.post("/api/dataset/entries", json=payload)
    
    # Now check stats
    response = client.get("/api/dataset/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_entries"] == 1
    assert stats["validated_entries"] == 1
    assert isinstance(stats["by_language"], dict)
    # by_language aggregates by target_language
    assert "mun" in stats["by_language"]
    assert stats["by_language"]["mun"] == 1
