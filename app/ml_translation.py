import os
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


BACKEND = os.getenv("BHASHA_MODEL_BACKEND", "indictrans2").lower()
INDICTRANS_MODEL = os.getenv(
    "BHASHA_MODEL_NAME", "ai4bharat/indictrans2-indic-indic-dist-320M"
)
BACKUP_MODEL = os.getenv(
    "BHASHA_BACKUP_MODEL_NAME",
    "google/madlad400-3b-mt",
)


@lru_cache(maxsize=1)
def _load_indictrans_engine():
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    from IndicTransToolkit.processor import IndicProcessor

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(INDICTRANS_MODEL, trust_remote_code=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(INDICTRANS_MODEL, trust_remote_code=True)
    model.to(device)
    model.eval()
    return model, tokenizer, IndicProcessor(inference=True), device


@lru_cache(maxsize=1)
def _load_backup_engine():
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(BACKUP_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(BACKUP_MODEL)
    model.to(device)
    model.eval()
    return model, tokenizer, device


def translate_to_santali(
    text: str, source_language: str, model_backend: str | None = None
) -> tuple[str, str]:
    """Translate one sentence with IndicTrans2, loading the model on first use."""
    import torch

    if source_language not in {"hi", "sat"}:
        raise ValueError("The prototype currently accepts Hindi or Santali input.")
    if source_language == "sat":
        return text, "identity"

    selected_backend = (model_backend or BACKEND).lower()
    if selected_backend not in {"indictrans2", "backup"}:
        raise ValueError(f"Unknown model backend: {selected_backend}")

    source_code = "hin_Deva"
    target_code = "sat_Olck"
    if selected_backend == "backup":
        model, tokenizer, device = _load_backup_engine()
        encoded = tokenizer(
            f"<2sat> {text}",
            truncation=True,
            max_length=256,
            return_tensors="pt",
        )
        encoded = {key: value.to(device) for key, value in encoded.items()}
        with torch.inference_mode():
            generated = model.generate(
                **encoded,
                max_length=256,
                num_beams=4,
            )
        result = tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip()
        return result, BACKUP_MODEL

    model, tokenizer, processor, device = _load_indictrans_engine()
    prepared = processor.preprocess_batch(
        [text], src_lang=source_code, tgt_lang=target_code
    )
    encoded = tokenizer(
        prepared,
        truncation=True,
        padding=True,
        max_length=256,
        return_tensors="pt",
    )
    encoded = {key: value.to(device) for key, value in encoded.items()}
    with torch.inference_mode():
        generated = model.generate(**encoded, max_length=256, num_beams=4)
    decoded = tokenizer.batch_decode(generated, skip_special_tokens=True)
    result = processor.postprocess_batch(decoded, lang=target_code)[0].strip()
    return result, INDICTRANS_MODEL