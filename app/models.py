from datetime import datetime
from typing import Optional
import os

from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

# Use file-based database for testing (ensures single instance), production uses file too
if os.getenv("TESTING") == "true":
    DATABASE_URL = "sqlite:///./test_bhasha_setu.db"
else:
    DATABASE_URL = "sqlite:///./bhasha_setu.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DatasetEntry(Base):
    __tablename__ = "dataset_entries"

    id = Column(Integer, primary_key=True, index=True)
    source_language = Column(String(10), index=True, default="hi")
    target_language = Column(String(10), index=True)
    domain = Column(String(50), index=True)
    source_text = Column(Text)
    target_text = Column(Text)
    validated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"

    id = Column(Integer, primary_key=True, index=True)
    language_code = Column(String(10), index=True)
    english_term = Column(String(255), index=True)
    native_term = Column(String(255))
    domain = Column(String(50), index=True)
    definition = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class LanguagePack(Base):
    __tablename__ = "language_packs"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True)
    name = Column(String(100))
    maturity = Column(String(50), default="prototype")
    model_version = Column(String(50))
    glossary_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db() -> None:
    """Initialize all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
