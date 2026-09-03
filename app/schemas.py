from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


LanguageCode = Literal["hi", "sat", "mun", "ho"]


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "BHASHA SETU"
    languages: list[str] = ["hi", "sat", "mun", "ho"]


class TranslationRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    source_text: str = Field(..., min_length=1, max_length=5000)
    source_language: LanguageCode = "hi"
    target_language: LanguageCode = "sat"
    domain: str = "general"
    mode: Literal["education", "voice", "offline"] = "education"
    model_backend: Literal["indictrans2", "backup"] | None = None


class TranslationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    translation: str
    source_text: str
    source_language: str
    target_language: str
    domain: str
    mode: str
    status: str
    model_version: str
    offline_ready: bool = True
    audio_available: bool = False


class LanguageEntry(BaseModel):
    code: str
    name: str
    native_name: str
    maturity: str
    glossary_count: int
    status: str = "active"


class LanguagePackSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    code: str
    name: str
    maturity: str
    glossary_count: int
    model_status: str
    offline_ready: bool
    language_level: str


class DatasetEntryCreate(BaseModel):
    source_language: LanguageCode = "hi"
    target_language: LanguageCode = "sat"
    domain: str = "general"
    source_text: str = Field(..., min_length=1, max_length=5000)
    target_text: str = Field(..., min_length=1, max_length=5000)
    validated: bool = False


class DatasetEntryRecord(BaseModel):
    id: int
    source_language: str
    target_language: str
    domain: str
    source_text: str
    target_text: str
    validated: bool
    created_at: str
    updated_at: str


class DatasetStats(BaseModel):
    total_entries: int
    validated_entries: int
    by_language: dict[str, int]


class GlossaryTermCreate(BaseModel):
    language_code: LanguageCode
    english_term: str = Field(..., min_length=1, max_length=255)
    native_term: str = Field(..., min_length=1, max_length=255)
    domain: str = "general"
    definition: str = Field(..., min_length=1, max_length=1000)


class GlossaryTermRecord(BaseModel):
    id: int
    language_code: str
    english_term: str
    native_term: str
    domain: str
    definition: str
    created_at: str


class LanguagePackCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    code: LanguageCode
    name: str = Field(..., min_length=1, max_length=100)
    maturity: str = "prototype"
    model_version: str = "1.0.0"
    glossary_count: int = 0


class LanguagePackRecord(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    code: str
    name: str
    maturity: str
    model_version: str
    glossary_count: int
    created_at: str
