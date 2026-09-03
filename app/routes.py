from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.models import get_db
from app.repository import (
    create_dataset_entry,
    list_dataset_entries,
    get_dataset_stats,
    create_glossary_term,
    list_glossary_terms,
)
from app.schemas import (
    DatasetEntryCreate,
    DatasetEntryRecord,
    DatasetStats,
    GlossaryTermCreate,
    GlossaryTermRecord,
    HealthResponse,
    LanguageEntry,
    LanguagePackSummary,
    TranslationRequest,
    TranslationResponse,
)
from app.services import get_language_pack_summaries, get_supported_languages, translate_text

api_router = APIRouter()


@api_router.get("/health", response_model=HealthResponse)
async def health() -> dict:
    return {
        "status": "ok",
        "app": "BHASHA SETU",
        "languages": ["hi", "sat", "mun", "ho"],
    }


@api_router.get("/languages", response_model=list[LanguageEntry])
async def languages() -> list[dict]:
    return get_supported_languages()


@api_router.post("/translate", response_model=TranslationResponse)
async def translate(payload: TranslationRequest) -> dict:
    result = translate_text(
        source_text=payload.source_text,
        source_language=payload.source_language,
        target_language=payload.target_language,
        domain=payload.domain,
        mode=payload.mode,
        model_backend=payload.model_backend,
    )
    return result


@api_router.get("/language-packs", response_model=list[LanguagePackSummary])
async def language_packs() -> list[dict]:
    return get_language_pack_summaries()


@api_router.post(
    "/dataset/entries",
    response_model=DatasetEntryRecord,
    status_code=status.HTTP_201_CREATED,
)
async def create_dataset_entry_endpoint(
    payload: DatasetEntryCreate,
    db: Session = Depends(get_db),
) -> dict:
    entry = create_dataset_entry(
        db=db,
        source_language=payload.source_language,
        target_language=payload.target_language,
        domain=payload.domain,
        source_text=payload.source_text,
        target_text=payload.target_text,
        validated=payload.validated,
    )
    return {
        "id": entry.id,
        "source_language": entry.source_language,
        "target_language": entry.target_language,
        "domain": entry.domain,
        "source_text": entry.source_text,
        "target_text": entry.target_text,
        "validated": entry.validated,
        "created_at": entry.created_at.isoformat(),
        "updated_at": entry.updated_at.isoformat(),
    }


@api_router.get("/dataset/entries", response_model=list[DatasetEntryRecord])
async def list_dataset_entries_endpoint(db: Session = Depends(get_db)) -> list[dict]:
    entries = list_dataset_entries(db)
    return [
        {
            "id": item.id,
            "source_language": item.source_language,
            "target_language": item.target_language,
            "domain": item.domain,
            "source_text": item.source_text,
            "target_text": item.target_text,
            "validated": item.validated,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        }
        for item in entries
    ]


@api_router.get("/dataset/stats", response_model=DatasetStats)
async def dataset_stats_endpoint(db: Session = Depends(get_db)) -> dict:
    return get_dataset_stats(db)


@api_router.post(
    "/glossary/terms",
    response_model=GlossaryTermRecord,
    status_code=status.HTTP_201_CREATED,
)
async def create_glossary_term_endpoint(
    payload: GlossaryTermCreate,
    db: Session = Depends(get_db),
) -> dict:
    term = create_glossary_term(
        db=db,
        language_code=payload.language_code,
        english_term=payload.english_term,
        native_term=payload.native_term,
        domain=payload.domain,
        definition=payload.definition,
    )
    return {
        "id": term.id,
        "language_code": term.language_code,
        "english_term": term.english_term,
        "native_term": term.native_term,
        "domain": term.domain,
        "definition": term.definition,
        "created_at": term.created_at.isoformat(),
    }


@api_router.get("/glossary/terms", response_model=list[GlossaryTermRecord])
async def list_glossary_terms_endpoint(
    language_code: str = None,
    domain: str = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    terms = list_glossary_terms(db, language_code=language_code, domain=domain)
    return [
        {
            "id": item.id,
            "language_code": item.language_code,
            "english_term": item.english_term,
            "native_term": item.native_term,
            "domain": item.domain,
            "definition": item.definition,
            "created_at": item.created_at.isoformat(),
        }
        for item in terms
    ]
