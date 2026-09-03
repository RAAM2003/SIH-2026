import pytest

from main import app


def test_glossary_term_creation(client):
    """Test creating a glossary term."""
    payload = {
        "language_code": "sat",
        "english_term": "addition",
        "native_term": "ᱡᱩᱨ",
        "domain": "mathematics",
        "definition": "The process of combining two or more numbers",
    }
    
    response = client.post("/api/glossary/terms", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["language_code"] == "sat"
    assert created["english_term"] == "addition"
    assert created["native_term"] == "ᱡᱩᱨ"
    assert created["domain"] == "mathematics"
    assert "id" in created
    assert "created_at" in created


def test_glossary_term_listing(client):
    """Test listing all glossary terms."""
    # Create multiple terms
    terms_data = [
        {
            "language_code": "sat",
            "english_term": "number",
            "native_term": "ᱞᱮᱠᱷᱟ",
            "domain": "mathematics",
            "definition": "A symbol or name for a quantity",
        },
        {
            "language_code": "mun",
            "english_term": "school",
            "native_term": "पाठशाला",
            "domain": "education",
            "definition": "An institution for learning",
        },
    ]
    
    for term in terms_data:
        client.post("/api/glossary/terms", json=term)
    
    # List all terms
    response = client.get("/api/glossary/terms")
    assert response.status_code == 200
    terms = response.json()
    assert len(terms) == 2
    assert isinstance(terms, list)


def test_glossary_filter_by_language(client):
    """Test filtering glossary terms by language code."""
    # Create terms in different languages
    client.post(
        "/api/glossary/terms",
        json={
            "language_code": "sat",
            "english_term": "water",
            "native_term": "ᱜ",
            "domain": "nature",
            "definition": "Essential liquid for life",
        },
    )
    client.post(
        "/api/glossary/terms",
        json={
            "language_code": "ho",
            "english_term": "water",
            "native_term": "जल",
            "domain": "nature",
            "definition": "Essential liquid for life",
        },
    )
    
    # Filter by language
    response = client.get("/api/glossary/terms?language_code=sat")
    assert response.status_code == 200
    terms = response.json()
    assert len(terms) == 1
    assert terms[0]["language_code"] == "sat"
    assert terms[0]["native_term"] == "ᱜ"


def test_glossary_filter_by_domain(client):
    """Test filtering glossary terms by domain."""
    # Create terms in different domains
    client.post(
        "/api/glossary/terms",
        json={
            "language_code": "sat",
            "english_term": "addition",
            "native_term": "ᱡᱩᱨ",
            "domain": "mathematics",
            "definition": "Sum operation",
        },
    )
    client.post(
        "/api/glossary/terms",
        json={
            "language_code": "sat",
            "english_term": "teacher",
            "native_term": "ᱚᱨᱡᱚ",
            "domain": "education",
            "definition": "Person who teaches",
        },
    )
    
    # Filter by domain
    response = client.get("/api/glossary/terms?domain=mathematics")
    assert response.status_code == 200
    terms = response.json()
    assert len(terms) == 1
    assert terms[0]["domain"] == "mathematics"
    assert terms[0]["english_term"] == "addition"


def test_glossary_filter_by_language_and_domain(client):
    """Test filtering glossary terms by both language and domain."""
    # Create several terms
    client.post(
        "/api/glossary/terms",
        json={
            "language_code": "sat",
            "english_term": "sum",
            "native_term": "ᱡᱩᱨ",
            "domain": "mathematics",
            "definition": "Result of addition",
        },
    )
    client.post(
        "/api/glossary/terms",
        json={
            "language_code": "sat",
            "english_term": "book",
            "native_term": "ᱯᱟᱛᱛᱚᱠ",
            "domain": "education",
            "definition": "Set of pages with text",
        },
    )
    client.post(
        "/api/glossary/terms",
        json={
            "language_code": "mun",
            "english_term": "sum",
            "native_term": "जोड़",
            "domain": "mathematics",
            "definition": "Result of addition",
        },
    )
    
    # Filter by language and domain
    response = client.get("/api/glossary/terms?language_code=sat&domain=mathematics")
    assert response.status_code == 200
    terms = response.json()
    assert len(terms) == 1
    assert terms[0]["language_code"] == "sat"
    assert terms[0]["domain"] == "mathematics"
    assert terms[0]["english_term"] == "sum"


def test_glossary_fln_vocabulary(client):
    """Test FLN (Foundation Level Numeracy) vocabulary endpoint."""
    # Create FLN-specific vocabulary
    fln_terms = [
        {
            "language_code": "sat",
            "english_term": "one",
            "native_term": "ᱢᱤᱫ",
            "domain": "fln",
            "definition": "Number 1",
        },
        {
            "language_code": "sat",
            "english_term": "two",
            "native_term": "ᱵᱟᱨ",
            "domain": "fln",
            "definition": "Number 2",
        },
        {
            "language_code": "mun",
            "english_term": "one",
            "native_term": "मिद",
            "domain": "fln",
            "definition": "Number 1",
        },
    ]
    
    for term in fln_terms:
        client.post("/api/glossary/terms", json=term)
    
    # Retrieve FLN vocabulary for Santali
    response = client.get("/api/glossary/terms?language_code=sat&domain=fln")
    assert response.status_code == 200
    terms = response.json()
    assert len(terms) == 2
    assert all(term["domain"] == "fln" for term in terms)
    assert all(term["language_code"] == "sat" for term in terms)
