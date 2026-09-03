from typing import Any


LANGUAGE_MAP = {
    "hi": {"name": "Hindi", "native_name": "हिन्दी", "maturity": "production"},
    "sat": {"name": "Santali", "native_name": "ᱥᱟᱱᱛᱟᱲᱤ", "maturity": "production"},
    "mun": {"name": "Mundari", "native_name": "मुण्डारी", "maturity": "prototype"},
    "ho": {"name": "Ho", "native_name": "ho", "maturity": "prototype"},
}


LANGUAGE_PACKS = [
    {
        "code": "sat",
        "name": "Santali",
        "maturity": "production",
        "glossary_count": 1850,
        "model_status": "active",
        "offline_ready": True,
        "language_level": "classroom-ready",
    },
    {
        "code": "mun",
        "name": "Mundari",
        "maturity": "prototype",
        "glossary_count": 1200,
        "model_status": "fine-tuning",
        "offline_ready": True,
        "language_level": "prototype",
    },
    {
        "code": "ho",
        "name": "Ho",
        "maturity": "prototype",
        "glossary_count": 1180,
        "model_status": "fine-tuning",
        "offline_ready": True,
        "language_level": "prototype",
    },
]


def get_supported_languages() -> list[dict[str, Any]]:
    return [
        {
            "code": code,
            "name": info["name"],
            "native_name": info["native_name"],
            "maturity": info["maturity"],
            "glossary_count": 0 if code == "hi" else 1200,
        }
        for code, info in LANGUAGE_MAP.items()
    ]


def translate_text(
    source_text: str,
    source_language: str,
    target_language: str,
    domain: str,
    mode: str,
    model_backend: str | None = None,
) -> dict[str, Any]:
    model_version = "bhasha-setu-demo"
    status = "completed"
    if target_language == "sat" and source_language in {"hi", "sat"}:
        try:
            from app.ml_translation import translate_to_santali

            translated, model_version = translate_to_santali(
                source_text, source_language, model_backend=model_backend
            )
        except (ImportError, OSError, RuntimeError, ValueError) as exc:
            if isinstance(exc, OSError) and any(
                marker in str(exc).lower()
                for marker in ("gated", "403", "authorized list", "access")
            ):
                translated = (
                    "IndicTrans2 access is still pending on Hugging Face. "
                    "Approve the model request, then restart the server."
                )
            elif isinstance(exc, ValueError):
                translated = str(exc)
            else:
                translated = source_text if source_language == "sat" else (
                    "Model setup is required for Hindi to Santali translation. "
                    f"Install the ML dependencies and retry. ({type(exc).__name__})"
                )
            model_version = "translation-model-unavailable"
            status = "model_unavailable"
    elif source_language == target_language:
        translated = source_text
    else:
        translated = (
            f"[{target_language.upper()}] "
            f"{source_text}"
            "\n\nThis is an education-aware draft translation prepared for the BHASHA SETU pipeline."
        )

    return {
        "translation": translated,
        "source_text": source_text,
        "source_language": source_language,
        "target_language": target_language,
        "domain": domain,
        "mode": mode,
        "status": status,
        "model_version": model_version,
        "offline_ready": True,
        "audio_available": target_language == "sat" and status == "completed",
    }


def get_language_pack_summaries() -> list[dict[str, Any]]:
    return LANGUAGE_PACKS
