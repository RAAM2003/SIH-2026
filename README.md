# BHASHA SETU

BHASHA SETU is a production-oriented education AI platform for multilingual translation and learning support across Hindi, Santali, Mundari, and Ho.

## Features

- **Education-aware translation pipeline** with language-specific adapters
- **Language pack management** for Santali, Mundari, and Ho with maturity tracking
- **Offline-ready architecture** for local deployment and classroom use
- **Real database persistence** with SQLAlchemy and SQLite for production data durability
- **Glossary and FLN vocabulary management** for education-specific terminology
- **Admin dashboard** for native-speaker dataset validation and annotation
- **Modular backend design** suitable for ML model adapters and speech integration
- **API-driven orchestration** for translation, language packs, and dataset operations

## Model integration

The current prototype uses a lazy-loaded pretrained translation model. Model
weights are downloaded on the first translation request and cached by Hugging
Face outside the repository, normally under `~/.cache/huggingface/hub/`.

The intended primary model is:

```text
ai4bharat/indictrans2-indic-indic-dist-320M
```

It is configured for Hindi (`hin_Deva`) to Santali in Ol Chiki (`sat_Olck`).
This model is gated, so the Hugging Face account used by the running server
must be approved for access. A valid login alone is not enough.

The adapter is implemented in `app/ml_translation.py` and is called lazily by
`app/services.py`; the application does not fine-tune the model or use the
files in `ml/datasets/` during inference.

### Temporary fallback

An experimental public fallback is available for Hindi-to-Santali inference:

```text
google/madlad400-3b-mt
```

It is public and uses the `<2sat>` target tag. It is a 3B-parameter model, so
it needs considerably more disk space and memory than the primary distilled
model. Select it with:

```bash
BHASHA_MODEL_BACKEND=backup python -m uvicorn main:app --reload
```

The default backend remains IndicTrans2:

```bash
python -m uvicorn main:app --reload
```

Until access is approved, the API returns `model_unavailable` with an access
message rather than presenting untranslated or incorrect text as Santali.

### Switching models with `.env`

Create the local environment file once:

```bash
cp .env.example .env
```

For the default IndicTrans2 backend, set:

```env
BHASHA_MODEL_BACKEND=indictrans2
BHASHA_MODEL_NAME=ai4bharat/indictrans2-indic-indic-dist-320M
```

For the experimental backup backend, set:

```env
BHASHA_MODEL_BACKEND=backup
BHASHA_BACKUP_MODEL_NAME=thunderboltc/nllb-200-distilled-santali-sanlish-bangla-lr2e3
```

Restart the server after editing `.env`:

```bash
source venv/bin/activate
python -m uvicorn main:app --reload
```

The fallback is intended for prototype inference. Review its translations
before using them as educational content.

The translator page also provides a model dropdown. `IndicTrans2 (default)`
and `MADLAD-400 (public fallback)` are sent as `model_backend` with each
translation request. The dropdown selection overrides `BHASHA_MODEL_BACKEND`
for that request; `.env` remains the default when an API client omits the
field.

## Architecture

- **FastAPI** backend with async support
- **SQLAlchemy ORM** with SQLite for persistent data storage
- **Pydantic** validation and schemas
- **Jinja2** templates for web UI
- **Modular service layer** for language packs and translations
- **Admin dashboard** for dataset management and glossary curation

## Database

The app uses SQLite for persistence with the following tables:
- `dataset_entries` - Translation pairs for model training
- `glossary_terms` - FLN vocabulary and language-specific terminology
- `language_packs` - Language model versions and metadata

## Quick start

```bash
cd application
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Then open:
- http://127.0.0.1:8000/ (landing page)
- http://127.0.0.1:8000/admin (dataset validation dashboard)
- http://127.0.0.1:8000/docs (API documentation)

## API overview

### Core endpoints
- `GET /api/health` - System health status
- `GET /api/languages` - Supported language registry
- `POST /api/translate` - Education-aware translation
- `GET /api/language-packs` - Language maturity and pack summary

### Dataset management
- `POST /api/dataset/entries` - Submit validated translation pairs
- `GET /api/dataset/entries` - List all dataset entries
- `GET /api/dataset/stats` - Dataset statistics by language

### Glossary management
- `POST /api/glossary/terms` - Add FLN vocabulary terms
- `GET /api/glossary/terms` - List glossary with filtering

## Testing

```bash
pytest tests/test_api.py        # Core API tests (4/4 passing ✅)
pytest tests/test_dataset_admin.py  # Dataset integration tests (2/2 passing ✅)
pytest tests/test_glossary.py   # Glossary/FLN vocabulary tests (6/6 passing ✅)
pytest                          # Full test suite (12/12 passing ✅)
```

All tests use file-based SQLite database for reliable test isolation.

## Production roadmap

1. ✅ API foundation with health, languages, translation, language-packs endpoints
2. ✅ SQLAlchemy database models and persistence layer (3 tables: dataset_entries, glossary_terms, language_packs)
3. ✅ Admin dashboard for dataset validation
4. ✅ Glossary and FLN vocabulary management (complete with filtering by language and domain)
5. ✅ Full test suite (12 tests, all passing)
6. ✅ Pretrained IndicTrans2 adapter and prototype Hindi-to-Santali UI
7. Integrate native-language speaker validation workflows
8. Integrate ASR and TTS specialized models
9. Add offline model packaging for Android deployment
10. Attach advanced dataset pipelines and model training

## Development

All code follows production standards with:
- Type hints throughout
- Pydantic validation
- Structured logging
- Error handling
- CORS support
- OpenAPI documentation

## Next steps for contributors

1. **ML Integration**: Test IndicTrans2 after gated-model access is approved
2. **Glossary Enhancement**: Add glossary term matching to translation layer
3. **Test Isolation**: Fix database test setup for proper test isolation
4. **Admin UI**: Expand dashboard with glossary management interface
5. **Speech Pipeline**: Connect ASR/TTS models to the translation endpoints
