from sqlalchemy.orm import Session
from app.models import DatasetEntry, GlossaryTerm, LanguagePack, init_db


def initialize_database() -> None:
    """Initialize the database schema."""
    init_db()


def create_dataset_entry(
    db: Session,
    source_language: str,
    target_language: str,
    domain: str,
    source_text: str,
    target_text: str,
    validated: bool,
) -> DatasetEntry:
    """Create and persist a new dataset entry."""
    entry = DatasetEntry(
        source_language=source_language,
        target_language=target_language,
        domain=domain,
        source_text=source_text,
        target_text=target_text,
        validated=validated,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_dataset_entries(db: Session, limit: int = 100) -> list[DatasetEntry]:
    """List all dataset entries."""
    return db.query(DatasetEntry).limit(limit).all()


def get_dataset_stats(db: Session) -> dict:
    """Get dataset statistics."""
    total = db.query(DatasetEntry).count()
    validated = db.query(DatasetEntry).filter(DatasetEntry.validated == True).count()
    
    by_language = {}
    for entry in db.query(DatasetEntry.target_language).distinct():
        lang = entry.target_language
        count = db.query(DatasetEntry).filter(DatasetEntry.target_language == lang).count()
        by_language[lang] = count
    
    return {
        "total_entries": total,
        "validated_entries": validated,
        "by_language": by_language,
    }


def create_glossary_term(
    db: Session,
    language_code: str,
    english_term: str,
    native_term: str,
    domain: str,
    definition: str,
) -> GlossaryTerm:
    """Create a new glossary term."""
    term = GlossaryTerm(
        language_code=language_code,
        english_term=english_term,
        native_term=native_term,
        domain=domain,
        definition=definition,
    )
    db.add(term)
    db.commit()
    db.refresh(term)
    return term


def list_glossary_terms(db: Session, language_code: str = None, domain: str = None, limit: int = 100) -> list[GlossaryTerm]:
    """List glossary terms with optional filtering."""
    query = db.query(GlossaryTerm)
    if language_code:
        query = query.filter(GlossaryTerm.language_code == language_code)
    if domain:
        query = query.filter(GlossaryTerm.domain == domain)
    return query.limit(limit).all()


def get_language_packs(db: Session) -> list[LanguagePack]:
    """Get all language packs."""
    return db.query(LanguagePack).all()
