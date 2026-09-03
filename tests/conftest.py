import os
import pytest
from fastapi.testclient import TestClient

# Set TESTING environment variable BEFORE any imports
os.environ["TESTING"] = "true"

# Import models AFTER setting env var (ensures in-memory database is used)
from app.models import Base, get_db, engine, SessionLocal
from main import app


def override_get_db():
    """Override dependency to use test database."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply the dependency override
app.dependency_overrides[get_db] = override_get_db

# Setup: Create all tables in the test database
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def reset_database():
    """Clear all tables before each test for isolation."""
    # Delete all data
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    yield


@pytest.fixture
def client():
    """Provide a test client for each test."""
    return TestClient(app)
