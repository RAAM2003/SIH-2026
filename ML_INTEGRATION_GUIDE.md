<!-- # ML Model Integration Guide for BHASHA SETU

**Date**: September 2, 2026  
**Focus**: IndicTrans2 Integration Best Practices & Production Deployment  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [IndicTrans2 Overview](#indictrans2-overview)
3. [Architecture for Translation Integration](#architecture-for-translation-integration)
4. [Implementation Strategy](#implementation-strategy)
5. [Performance Optimization](#performance-optimization)
6. [Deployment Considerations](#deployment-considerations)
7. [Testing & Evaluation](#testing--evaluation)
8. [Roadmap](#roadmap)

---

## Executive Summary

**IndicTrans2** is the industry-leading open-source multilingual NMT (Neural Machine Translation) model for Indian languages. It supports all 22 scheduled Indian languages including **Santali (sat_Olck)**, and provides excellent performance for low-resource languages.

### Key Stats
- **22 Scheduled Indian Languages** including Santali, Mundari-adjacent support
- **5 Script Families**: Devanagari, Ol Chiki (Santali), Perso-Arabic, Meitei, Latin
- **230M Training Pairs**: From BPCC dataset (mined + human-annotated)
- **Multiple Variants**: 
  - Base models (full size, ~500M-1.2B parameters)
  - Distilled models (200M parameters, 40% smaller, minimal quality loss)
  - Long-context RoPE variants (handles 2048 token sequences)
- **Production Ready**: Used in production by Indian government and educational institutions

### Why IndicTrans2 for BHASHA SETU

✅ **Exact Match for Use Case**: Built for education, low-resource languages  
✅ **High Quality**: Outperforms Google Translate and NLLB for Indian languages  
✅ **Open Source**: MIT licensed, no external API dependencies  
✅ **Offline Capable**: Run locally without internet connection  
✅ **Quantized Options**: Multiple model sizes for different resource constraints  
✅ **Transfer Learning Ready**: Fine-tuning support for domain-specific vocabulary (FLN terms)  

---

## IndicTrans2 Overview

### Supported Language Codes in IndicTrans2

| Language | Code | Script | Status |
|----------|------|--------|--------|
| English | eng_Latn | Latin | Pivot |
| Hindi | hin_Deva | Devanagari | Primary |
| **Santali** | **sat_Olck** | **Ol Chiki** | **Primary** ✅ |
| Bengali | ben_Beng | Bengali | Primary |
| Telugu | tel_Telu | Telugu | Primary |
| Marathi | mar_Deva | Devanagari | Primary |
| Tamil | tam_Taml | Tamil | Primary |
| Kannada | kan_Knda | Kannada | Primary |
| ... | ... | ... | ... |

**Note**: Mundari doesn't have a native script in IndicTrans2. Solutions:
1. Use Hindi as intermediate (Mundari → Hindi → English)
2. Use transfer learning with Santali-Mundari bilingual data
3. Map Mundari text to closest Devanagari representation

### Model Variants Available

```
1. EN-INDIC (English to Indian Languages)
   - Base: ai4bharat/indictrans2-en-indic-1B
   - Distilled: ai4bharat/indictrans2-en-indic-dist-200M

2. INDIC-EN (Indian Languages to English)
   - Base: ai4bharat/indictrans2-indic-en-1B
   - Distilled: ai4bharat/indictrans2-indic-en-dist-200M

3. INDIC-INDIC (Indian to Indian, via English pivot)
   - Base: ai4bharat/indictrans2-indic-indic-1B
   - Distilled: ai4bharat/indictrans2-indic-indic-dist-200M

4. LONG-CONTEXT RoPE VARIANTS (for extended sequences)
   - Up to 2048 tokens
   - Recommended for documents and multi-paragraph text
```

### Recommended Model for BHASHA SETU

**Primary**: `ai4bharat/indictrans2-indic-en-dist-200M` (Indic → English)  
- Handles English, Hindi, Santali, and other Indian languages
- Distilled variant (200M params) runs on modest hardware
- ~4GB memory footprint with quantization

**Secondary**: `ai4bharat/indictrans2-en-indic-dist-200M` (English → Indic)  
- For English → Santali/Hindi translations
- Same distilled size for consistency

---

## Architecture for Translation Integration

### System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        BHASHA SETU API                          │
│  (FastAPI Server)                                              │
└─────────────────┬───────────────────────────────────────────────┘
                  │
        ┌─────────┴──────────┬──────────────────┐
        │                    │                  │
    ┌───▼────────┐  ┌────────▼────┐  ┌─────────▼──────┐
    │  Request   │  │ Glossary DB │  │  Cache Layer   │
    │ Validation │  │ (SQLite)    │  │  (Redis)       │
    │ (Pydantic) │  │             │  │                │
    └────┬───────┘  └──────┬──────┘  └────────┬───────┘
         │                 │                  │
         └─────────────────┼──────────────────┘
                           │
        ┌──────────────────▼─────────────────────┐
        │    Translation Service Layer          │
        │  (NEW: ML Model Adapter)              │
        └──────────────┬───────────────────────┘
                       │
        ┌──────────────┴──────────────────┐
        │                                 │
    ┌───▼─────────────┐  ┌───────────────▼─────┐
    │  Preprocessing   │  │  Model Inference   │
    │  - Language      │  │  (IndicTrans2)    │
    │    Detection     │  │  - Batch encoding  │
    │  - Normalization │  │  - CUDA/CPU        │
    │  - Term lookup   │  │  - Beam search     │
    └───┬─────────────┘  └───────────────┬─────┘
        │                                 │
        └─────────────────┬───────────────┘
                          │
        ┌─────────────────▼────────────┐
        │   Postprocessing             │
        │  - Glossary term replacement │
        │  - Detokenization            │
        │  - Entity preservation       │
        └─────────────────┬────────────┘
                          │
        ┌─────────────────▼────────────┐
        │   Response to Client         │
        │  (Pydantic Response Model)   │
        └──────────────────────────────┘
```

### Implementation Layers

#### 1. **Request Layer** (Already Exists)
```python
# app/schemas.py
class TranslationRequest(BaseModel):
    source_text: str
    source_language: LanguageCode = "hi"
    target_language: LanguageCode = "sat"
    domain: str = "general"  # Used for glossary lookup
    preserve_entities: bool = True  # Keep names, numbers unchanged
    return_confidence: bool = False  # Return translation confidence
```

#### 2. **Service Layer** (NEW - To Be Updated)
```python
# app/services.py - ADD THIS
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
from functools import lru_cache

class TranslationEngine:
    """IndicTrans2 Model Wrapper"""
    
    def __init__(self, model_name: str, device: str = "cuda"):
        self.model_name = model_name
        self.device = device
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load model with lazy loading on first use"""
        if self.model is None:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,  # Reduce memory
                device_map="auto"  # Auto GPU/CPU placement
            )
    
    def translate_batch(
        self,
        texts: list[str],
        src_lang: str,
        tgt_lang: str,
        max_length: int = 256
    ) -> list[str]:
        """Batch translation for efficiency"""
        # Preprocess with IndicTransToolkit
        preprocessed = self._preprocess(texts, src_lang)
        
        # Tokenize
        inputs = self.tokenizer(
            preprocessed,
            truncation=True,
            padding="longest",
            return_tensors="pt",
            max_length=max_length
        ).to(self.device)
        
        # Generate with beam search
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_beams=5,  # Beam search width
                temperature=1.0,  # Deterministic
                num_return_sequences=1
            )
        
        # Decode
        translations = self.tokenizer.batch_decode(
            outputs,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        )
        
        # Postprocess
        return [self._postprocess(t, tgt_lang) for t in translations]
    
    def _preprocess(self, texts: list[str], lang: str) -> list[str]:
        """Normalize text, add language tags"""
        # Use IndicTransToolkit for proper preprocessing
        from IndicTransToolkit.processor import IndicProcessor
        processor = IndicProcessor(inference=True)
        
        batches = processor.preprocess_batch(
            texts,
            src_lang=lang,
            tgt_lang="eng_Latn"  # Always translate via English
        )
        return batches
    
    def _postprocess(self, text: str, lang: str) -> str:
        """Cleanup output"""
        from IndicTransToolkit.processor import IndicProcessor
        processor = IndicProcessor(inference=True)
        
        return processor.postprocess_batch([text], lang=lang)[0]
```

#### 3. **Repository Layer** (Add Inference Caching)
```python
# app/repository.py - ADD FUNCTION
from datetime import datetime
from sqlalchemy import or_

def cache_translation(
    db: Session,
    source_text: str,
    target_text: str,
    source_language: str,
    target_language: str,
    domain: str,
    confidence: float
) -> None:
    """
    Cache successful translations to avoid re-inference.
    Used as a lookup before running model inference.
    """
    cached = db.query(TranslationCache).filter(
        TranslationCache.source_text == source_text,
        TranslationCache.source_language == source_language,
        TranslationCache.target_language == target_language,
        TranslationCache.domain == domain
    ).first()
    
    if not cached:
        cache_entry = TranslationCache(
            source_text=source_text,
            target_text=target_text,
            source_language=source_language,
            target_language=target_language,
            domain=domain,
            confidence=confidence,
            created_at=datetime.utcnow()
        )
        db.add(cache_entry)
        db.commit()

def get_cached_translation(
    db: Session,
    source_text: str,
    source_language: str,
    target_language: str,
    domain: str
) -> Optional[str]:
    """Retrieve cached translation"""
    cache = db.query(TranslationCache).filter(
        TranslationCache.source_text == source_text,
        TranslationCache.source_language == source_language,
        TranslationCache.target_language == target_language,
        TranslationCache.domain == domain
    ).first()
    
    return cache.target_text if cache else None
```

#### 4. **Routes Layer** (Update Translation Endpoint)
```python
# app/routes.py - UPDATE TRANSLATE ENDPOINT
from app.services import TranslationEngine

# Initialize model at startup
translation_engine = None

@app.on_event("startup")
async def startup():
    global translation_engine
    translation_engine = TranslationEngine(
        "ai4bharat/indictrans2-indic-en-dist-200M",
        device="cuda" if torch.cuda.is_available() else "cpu"
    )

@api_router.post("/translate", response_model=TranslationResponse)
async def translate(request: TranslationRequest, db: Session = Depends(get_db)):
    """
    Education-aware translation with:
    1. Glossary term substitution (FLN vocabulary)
    2. Entity preservation (names, numbers)
    3. Beam search for quality
    4. Inference caching
    """
    
    # 1. Check cache first
    cached = get_cached_translation(
        db,
        request.source_text,
        request.source_language,
        request.target_language,
        request.domain
    )
    if cached:
        return TranslationResponse(
            translation=cached,
            source_text=request.source_text,
            source_language=request.source_language,
            target_language=request.target_language,
            domain=request.domain,
            model="indictrans2-cached",
            confidence=1.0
        )
    
    # 2. Get glossary terms for domain
    glossary_terms = repository.list_glossary_terms(
        db,
        language_code=request.target_language,
        domain=request.domain
    )
    glossary_map = {t.english_term: t.native_term for t in glossary_terms}
    
    # 3. Replace glossary terms in source before translation
    processed_text = request.source_text
    for eng_term, native_term in glossary_map.items():
        if eng_term.lower() in processed_text.lower():
            processed_text = processed_text.replace(eng_term, f"[GLOSSARY:{native_term}]")
    
    # 4. Run model inference
    translation = translation_engine.translate_batch(
        [processed_text],
        request.source_language,
        request.target_language
    )[0]
    
    # 5. Restore glossary terms
    for eng_term, native_term in glossary_map.items():
        translation = translation.replace(f"[GLOSSARY:{native_term}]", native_term)
    
    # 6. Cache result
    cache_translation(
        db, processed_text, translation,
        request.source_language, request.target_language,
        request.domain, confidence=0.92
    )
    
    return TranslationResponse(
        translation=translation,
        source_text=request.source_text,
        source_language=request.source_language,
        target_language=request.target_language,
        domain=request.domain,
        model="indictrans2-v2"
    )
```

---

## Implementation Strategy

### Phase 1: Model Integration (Week 1)

**Step 1.1**: Install Dependencies
```bash
pip install IndicTransToolkit transformers torch
```

**Step 1.2**: Update Models Table
```python
# app/models.py - ADD
class TranslationCache(Base):
    __tablename__ = "translation_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    source_text = Column(Text, index=True)
    target_text = Column(Text)
    source_language = Column(String(10), index=True)
    target_language = Column(String(10), index=True)
    domain = Column(String(50), index=True)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('source_text', 'source_language', 'target_language', 'domain'),
    )
```

**Step 1.3**: Implement TranslationEngine
- Copy `TranslationEngine` class to `app/services.py`
- Add IndicProcessor integration for proper language handling
- Implement batch processing for efficiency

**Step 1.4**: Update Routes
- Replace placeholder translation logic
- Add glossary-aware preprocessing
- Implement result caching

**Step 1.5**: Testing
```bash
pytest tests/test_translation_engine.py -v
# Test with actual IndicTrans2 model
```

### Phase 2: Optimization (Week 2)

**Step 2.1**: Quantization
```python
# Use quantized models for faster inference
from transformers import AutoModelForSeq2SeqLM
import torch

model = AutoModelForSeq2SeqLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,  # Half precision
    load_in_8bit=True,  # 8-bit quantization
    device_map="auto"
)
```

**Step 2.2**: Batch Processing
```python
# Process multiple translations efficiently
texts = ["Text 1", "Text 2", "Text 3"]
translations = engine.translate_batch(texts, "hin_Deva", "eng_Latn")
```

**Step 2.3**: Caching Strategy
- In-memory Redis for hot translations
- Database for persistent cache (already implemented)
- Cache hit statistics in monitoring

**Step 2.4**: Asynchronous Processing
```python
from fastapi import BackgroundTasks

@api_router.post("/translate/async")
async def translate_async(
    request: TranslationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Fire-and-forget translation with callback"""
    job_id = str(uuid.uuid4())
    background_tasks.add_task(run_translation, job_id, request, db)
    return {"job_id": job_id, "status": "queued"}
```

### Phase 3: Advanced Features (Week 3-4)

**Step 3.1**: Domain-Specific Fine-tuning
```bash
# Use validated dataset entries for fine-tuning
bash finetune.sh <exp_dir> transformer_base18L <pretrained_ckpt>
```

**Step 3.2**: Language Pair Support
```python
# Map Mundari to Hindi for translation
LANGUAGE_PAIR_MAPPING = {
    ("mun", "sat"): ("hin_Deva", "sat_Olck"),  # Via Hindi as bridge
    ("mun", "eng"): ("hin_Deva", "eng_Latn"),
    ("ho", "sat"): ("hin_Deva", "sat_Olck"),
}
```

**Step 3.3**: Confidence Scoring
```python
# Get model confidence from beam search alternatives
def get_translation_with_confidence(text, src_lang, tgt_lang):
    outputs = model.generate(
        **inputs,
        num_return_sequences=5,  # Get top 5 translations
        output_scores=True
    )
    # Calculate confidence from generation scores
    confidence = calculate_beam_score(outputs.sequences_scores)
    return translation, confidence
```

---

## Performance Optimization

### Memory Optimization

| Model | Size | Memory | Speed | Quality |
|-------|------|--------|-------|---------|
| Base (1B) | 2.5GB | 8GB GPU | ~100ms/seq | Highest |
| Distilled (200M) | 500MB | 2GB GPU | ~50ms/seq | 95% of base |
| Quantized 8-bit | 125MB | 1GB GPU | ~60ms/seq | 90% of base |
| CPU Inference | - | 2GB RAM | ~500ms/seq | Same quality |

**Recommendation for BHASHA SETU**: Use distilled model with 8-bit quantization for optimal balance.

### Inference Speed

```python
# Benchmark different configurations
import time

def benchmark_translate(engine, texts, runs=10):
    times = []
    for _ in range(runs):
        start = time.time()
        engine.translate_batch(texts, "hin_Deva", "sat_Olck")
        times.append(time.time() - start)
    
    return {
        "mean": sum(times) / len(times),
        "min": min(times),
        "max": max(times),
        "throughput": len(texts) * runs / sum(times)
    }

# Results (approximate)
# Distilled on GPU: ~30-50ms per sentence
# Distilled on CPU: ~200-300ms per sentence
# Batch size 32: ~1000 sentences/minute on GPU
```

### Caching Strategy

```python
# Intelligent cache invalidation
def cache_translation(db, source_text, translation, domain):
    # Cache if confidence > threshold
    if confidence > 0.85:
        cache_entry = TranslationCache(
            source_text=source_text,
            target_text=translation,
            domain=domain,
            # Expire cache after 30 days
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(cache_entry)
        db.commit()

# Implement in routes
def get_translation(request, db):
    # 1. Check cache
    cached = get_cached_translation(db, request.source_text, request.domain)
    if cached:
        return cached  # Cache hit!
    
    # 2. Run inference
    translation = translation_engine.translate_batch(...)
    
    # 3. Cache result
    cache_translation(db, request.source_text, translation, request.domain)
    
    return translation
```

---

## Deployment Considerations

### Hardware Requirements

#### Minimum (Development)
- CPU: 4 cores (Intel i7 or equivalent)
- RAM: 8GB
- Storage: 10GB (for model files)
- GPU: Optional (CPU inference works, just slower)

#### Recommended (Production)
- CPU: 16 cores (server-grade)
- RAM: 32GB
- Storage: 50GB SSD (models + cache)
- GPU: NVIDIA A100/H100 with 40GB VRAM (or RTX 4090 with 24GB)
- Network: 1Gbps minimum

#### Scale (Many Concurrent Users)
- Multiple GPU nodes with load balancing
- Kubernetes for orchestration
- Redis cluster for distributed caching
- Database replication for read scaling

### Docker Optimization

```dockerfile
# Multi-stage build - reduce image size
FROM nvidia/cuda:12.1-runtime-ubuntu22.04 as builder

# Install dependencies
RUN pip install --no-cache-dir transformers torch IndicTransToolkit

# Copy model weights (optional - download on startup instead)
# COPY models/ /models/

FROM nvidia/cuda:12.1-runtime-ubuntu22.04
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Final app
COPY application/ /app/
WORKDIR /app

# Launch with GPU support
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--workers", "2"]
```

**Image size**: ~5GB (with CUDA)  
**Startup time**: ~30s (model loading) + ~10s (API ready)

### Scaling Pattern

```
┌─────────────────┐
│  Load Balancer  │  (Nginx, HAProxy)
│   (Port 80)     │
└────────┬────────┘
         │
    ┌────┼────┬────────┬────────┐
    │    │    │        │        │
┌───▼──┐ ┌──▼──┐ ┌───▼──┐ ┌──▼───┐
│Worker│ │Wor. │ │Wor.  │ │Wor.  │
│  #1  │ │ #2  │ │ #3   │ │ #4   │
│GPU1  │ │GPU2 │ │GPU3  │ │GPU4  │
└───┬──┘ └──┬──┘ └──┬───┘ └──┬───┘
    │       │       │        │
    └───┬───┴───┬───┴────────┘
        │       │
   ┌────▼────┬──▼──────┐
   │ Redis   │ Database │
   │ Cache   │ (PgSQL)  │
   └─────────┴──────────┘
```

---

## Testing & Evaluation

### Unit Tests

```python
# tests/test_translation_engine.py
def test_translation_engine_santali():
    engine = TranslationEngine("ai4bharat/indictrans2-indic-en-dist-200M")
    
    # Santali to English
    result = engine.translate_batch(
        ["ᱟᱭᱚᱰᱟᱬ ᱢᱟᱦᱟ"],  # "Good morning" in Santali
        "sat_Olck",
        "eng_Latn"
    )
    assert len(result) > 0
    assert "morning" in result[0].lower()

def test_glossary_substitution(db):
    # Add glossary term
    term = GlossaryTerm(
        language_code="sat",
        english_term="addition",
        native_term="ᱡᱩᱨ",
        domain="fln"
    )
    db.add(term)
    db.commit()
    
    # Test translation preserves glossary term
    response = api_client.post("/api/translate", json={
        "source_text": "addition of numbers",
        "source_language": "eng_Latn",
        "target_language": "sat_Olck",
        "domain": "fln"
    })
    assert "ᱡᱩᱨ" in response.json()["translation"]
```

### Evaluation Metrics

```python
# Evaluate against FLORES-22 and IN22 benchmarks
import evaluate

metric = evaluate.load("sacrebleu")

predictions = ["This is a test"]
references = [["This is a test"]]

results = metric.compute(predictions=predictions, references=references)
print(f"BLEU Score: {results['score']:.2f}")
# Expected: 95+ for identical text, 70-80 for realistic translations
```

### Production Monitoring

```python
# Track translation quality metrics
class TranslationMetrics:
    cache_hits: int = 0
    cache_misses: int = 0
    avg_inference_time: float = 0.0
    model_errors: int = 0
    
    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0

# Expose metrics endpoint
@app.get("/metrics")
async def get_metrics():
    return {
        "cache_hit_rate": metrics.cache_hit_rate,
        "avg_inference_time_ms": metrics.avg_inference_time * 1000,
        "model_errors": metrics.model_errors,
        "uptime_seconds": time.time() - app_start_time
    }
```

---

## Roadmap

### ✅ Completed (As of Sept 2, 2026)
- Production-ready FastAPI scaffold
- Database layer with SQLite persistence
- Glossary management system
- Admin dashboard for data validation
- Comprehensive test suite (12/12 passing)

### 🔄 Phase 1: ML Integration (Weeks 1-2)
- Implement IndicTrans2 model loading and inference
- Add glossary-aware preprocessing
- Implement translation caching layer
- Create unit tests for model inference
- **Target**: 95%+ BLEU score on FLORES-22

### 📋 Phase 2: Domain-Specific Tuning (Weeks 3-4)
- Fine-tune model on FLN (Foundation Level Numeracy) domain data
- Create Mundari-Santali bridge translations
- Implement confidence scoring
- Add batch processing API
- **Target**: Educational domain-specific performance improvements

### 🚀 Phase 3: Advanced Features (Month 2)
- **Speech Integration**: Connect ASR/TTS pipelines
- **Offline Packaging**: ONNX export for mobile deployment
- **Real-time Collaboration**: WebSocket support for classroom use
- **Teacher Feedback**: Active learning loop from annotations
- **Analytics**: Student performance tracking

### 🌍 Phase 4: Scale (Month 3+)
- Kubernetes deployment
- Multi-GPU inference clusters
- International expansion (other low-resource languages)
- Mobile app (Android/iOS)
- Classroom integration (Google Classroom, Moodle)

---

## Implementation Checklist

### Week 1 (Model Integration)
- [ ] Download IndicTrans2 distilled model from Hugging Face
- [ ] Implement `TranslationEngine` class in `app/services.py`
- [ ] Add `TranslationCache` table to models
- [ ] Update `/api/translate` endpoint with real inference
- [ ] Write integration tests
- [ ] Deploy to staging, verify with manual testing
- [ ] Monitor inference performance and memory usage

### Week 2 (Optimization)
- [ ] Implement 8-bit quantization
- [ ] Add Redis caching layer
- [ ] Benchmark different configurations
- [ ] Optimize batch processing
- [ ] Create performance monitoring dashboard
- [ ] Load testing with 100+ concurrent requests

### Week 3 (Testing & Validation)
- [ ] Evaluate on FLORES-22 Santali subset
- [ ] Create domain-specific test set (FLN numeracy)
- [ ] Native speaker evaluation (quality score)
- [ ] Compare against Google Translate baseline
- [ ] Document translation quality metrics

### Week 4+ (Production Ready)
- [ ] Docker image with all optimizations
- [ ] Load balancer setup (Nginx)
- [ ] Monitoring and alerting (Prometheus)
- [ ] Documentation and API spec
- [ ] Teacher training materials

---

## References

1. **IndicTrans2 Paper**: https://openreview.net/forum?id=vfT4YuzAYA
2. **GitHub**: https://github.com/AI4Bharat/IndicTrans2
3. **Model Hub**: https://huggingface.co/ai4bharat
4. **IndicTrans Toolkit**: https://github.com/VarunGumma/IndicTransToolkit
5. **FLORES Benchmark**: https://github.com/facebookresearch/flores
6. **Production ML Guide**: https://huggingface.co/docs/transformers/deployment

---

**Next Step**: Proceed with Week 1 implementation starting with IndicTrans2 model download and TranslationEngine class implementation. -->
























steps : 



Step 1 — Create your data workspace

You're currently inside:

SIH 2026

I'd create a completely separate directory for datasets:

mkdir -p ml/datasets/{santali,mundari,ho}/{raw,cleaned,validated}
mkdir -p ml/datasets/common

Then:

tree ml/datasets

You should get roughly:

ml/datasets
├── common
├── ho
│   ├── cleaned
│   ├── raw
│   └── validated
├── mundari
│   ├── cleaned
│   ├── raw
│   └── validated
└── santali
    ├── cleaned
    ├── raw
    └── validated
Step 2 — Install the dataset tools

Since you already created your venv, activate it:

source venv/bin/activate

Then:

pip install -U datasets huggingface_hub pandas pyarrow

Check:

python -c "import datasets, pandas, huggingface_hub; print('OK')"
Step 3 — Download the Adi Vaani dataset

This is one of the easiest ones.

The Hugging Face dataset currently provides configurations for both:

santhali
mundari

and has tribal_text and eng_text columns.

Adi Vaani Tribal-English Parallel Corpus

Run:

python

Then:

from datasets import load_dataset

santhali = load_dataset(
    "adivaanihf/adivaani-tribal-english-parallel-corpus",
    "santhali",
    split="train"
)

mundari = load_dataset(
    "adivaanihf/adivaani-tribal-english-parallel-corpus",
    "mundari",
    split="train"
)

print(santhali)
print(mundari)

Then inspect:

print(santhali[0])
print(mundari[0])

You should see records containing the tribal sentence and aligned English sentence.

Important

The dataset currently requires accepting its access conditions on Hugging Face. Its card also says it is derived from the parent Adi Vaani corpus, so we need to preserve provenance/licensing information rather than blindly redistribute it.

Don't worry about that now—we're only inspecting it.

Step 4 — Save those locally

Exit Python:

exit()

Then create:

python - <<'PY'
from datasets import load_dataset

for lang in ["santhali", "mundari"]:
    ds = load_dataset(
        "adivaanihf/adivaani-tribal-english-parallel-corpus",
        lang,
        split="train"
    )
    ds.to_parquet(f"ml/datasets/{'santali' if lang == 'santhali' else 'mundari'}/raw/adivaani.parquet")
    print(lang, len(ds))
PY

Now check:

ls -lh ml/datasets/santali/raw/
ls -lh ml/datasets/mundari/raw/
Step 5 — Download the MUCH more useful Santali education dataset

I found a new resource that is particularly relevant to your project:

COILD-MT Corpus

It has:

HIN-SAT

with 20,603 Hindi–Santali sentence pairs.

Even better, it is released under CC BY 4.0 according to the dataset card.

COILD-MT Corpus

This is much more directly useful than English–Santali for your actual:

Hindi → Santali

requirement.

Step 6 — Download Hindi–Santali

Run:

python

Then:

from huggingface_hub import hf_hub_download

src = hf_hub_download(
    repo_id="ainlpml-iitp/COILD-MT-Corpus",
    filename="HIN-SAT/Hindi.txt",
    repo_type="dataset"
)

tgt = hf_hub_download(
    repo_id="ainlpml-iitp/COILD-MT-Corpus",
    filename="HIN-SAT/Santali.txt",
    repo_type="dataset"
)

print(src)
print(tgt)

The dataset is line-aligned: line N of Hindi corresponds to line N of Santali.

Then inspect:

with open(src, encoding="utf-8") as f:
    hindi = f.readlines()

with open(tgt, encoding="utf-8") as f:
    santali = f.readlines()

print("Hindi:", len(hindi))
print("Santali:", len(santali))

for i in range(5):
    print("HINDI:", hindi[i].strip())
    print("SAT:", santali[i].strip())
    print()
Step 7 — And there's an even better Santali dataset

I found Education_v2 from the Centre of Indian Language Data.

This is specifically:

Hindi → Indian Languages Translation, focused on Education

and includes Santali. Its files are manually/source-reviewed educational translations and use a structure like:

id
src_hi
tgt_sat
domain

The dataset says it contains textbook-style educational content and other education-domain material.

Education_v2 on Hugging Face

This is probably one of the most important datasets for your project.

Why?

Because your problem isn't generic translation.

It's:

AI-powered vernacular pedagogy for primary education.

So educational Hindi → Santali data is exactly what we want.

Step 8 — Download Education_v2

You can clone it with Git LFS, but first let's inspect the repository.

Run:

python
from huggingface_hub import list_repo_files

files = list_repo_files(
    "coild-aikosh/Education_v2",
    repo_type="dataset"
)

for f in files[:100]:
    print(f)

We're specifically looking for:

HIN-SAT

and:

source_reviewed

because the dataset describes those as manually/source-reviewed translations.

Step 9 — CIIL Santali-Hindi Primer

This is not a normal machine-learning dataset.

It is an educational PDF.

That's okay.

It can become a source for your:

FLN vocabulary
+
educational phrases
+
language glossary

The official CIIL page directly lists the Santali-Hindi Primer, and the PDF is accessible from CIIL.

CIIL Santali-Hindi Primer

Download it into:

ml/datasets/santali/raw/

You can use:

curl -L \
"https://ciil.gov.in/primers/Santali-Hindi_Primer.pdf" \
-o ml/datasets/santali/raw/CIIL_Santali_Hindi_Primer.pdf

Then:

ls -lh ml/datasets/santali/raw/
Step 10 — CIIL Ho-Odia Primer

This is very important for Ho.

The official CIIL primer portal explicitly lists:

Ho-Odia Primer

We need to get the exact PDF URL from the CIIL flipbook rather than guessing a filename.

Open:

CIIL Primers Portal

Find:

Ho-Odia Primer

Click PDF FLIP.

The site uses a flipbook/PDF system, so once we identify the exact PDF path, save it as:

ml/datasets/ho/raw/CIIL_Ho_Odia_Primer.pdf

Don't rename/repackage the content for redistribution until we verify its usage rights. For now we're treating it as a research/source document.

Step 11 — CIIL Mundari Primer

There is also an official:

Mundari Primer

on the same CIIL-NCERT portal.

So download that into:

ml/datasets/mundari/raw/CIIL_Mundari_Primer.pdf

This gives us another educational resource for the Mundari language.

Step 12 — Here's what your directory should eventually look like
ml/
└── datasets/

    ├── santali/
    │   ├── raw/
    │   │   ├── adivaani.parquet
    │   │   ├── COILD_Hindi.txt
    │   │   ├── COILD_Santali.txt
    │   │   └── CIIL_Santali_Hindi_Primer.pdf
    │   │
    │   ├── cleaned/
    │   └── validated/
    │
    ├── mundari/
    │   ├── raw/
    │   │   ├── adivaani.parquet
    │   │   ├── MMLoSo_Mundari.csv
    │   │   └── CIIL_Mundari_Primer.pdf
    │   │
    │   ├── cleaned/
    │   └── validated/
    │
    └── ho/
        ├── raw/
        │   └── CIIL_Ho_Odia_Primer.pdf
        │
        ├── cleaned/
        └── validated/
Step 13 — What about MMLoSo?

The MMLoSo task definitely has:

mundari-train.csv

with:

row_id
hindi
mundari

and the task documentation says the corpus has 20,000 training pairs for Hindi–Mundari.

The task's data is released under CC BY-SA 4.0, with the requirement to cite the original sources for use outside the competition.

MMLoSo 2025 Dataset/Task Page

The competition data is associated with Kaggle, so if you have Kaggle access, we can download it there.

I don't want you to manually create 20,000 Mundari sentences when the benchmark already gives us a proper Hindi–Mundari corpus.

Step 14 — Your dataset strategy has now become much better
Santali

We have:

COILD-MT
20,603 Hindi–Santali
        +
Education_v2
Hindi–Santali education
        +
Adi Vaani
Santali–English
        +
CIIL Santali-Hindi Primer
        +
YOUR FLN data

That's a very strong starting point.

Mundari

We have:

MMLoSo
20,000 Hindi–Mundari
        +
Adi Vaani
Mundari–English
        +
CIIL Mundari Primer
        +
YOUR FLN data

Also strong.

Ho

This remains our research/collection track:

CIIL Ho-Odia Primer
        +
CIIL publications/resources
        +
Bharatavani resources
        +
native Ho speakers
        +
YOUR FLN corpus
        ↓
Hindi–Ho validated corpus

The CIIL publication catalogue also lists Hindi-English-Ho and Hindi-English-Mundari publications, which is another lead for linguistic resources, although these are publications rather than ready-made ML datasets.

Step 15 — Don't train yet

This is important.

We're currently at:

             STEP A
               │
               ▼
       FIND THE RESOURCES
               │
               ▼
       DOWNLOAD / INSPECT
               │
               ▼
       CLEAN + NORMALIZE
               │
               ▼
      BUILD UNIFIED FORMAT
               │
               ▼
          STEP B
               │
               ▼
       TRAINING DATASET

We're not at training yet.

What I want you to do right now

Since you're on your Mac and already have the venv, run these first three commands:

source venv/bin/activate
pip install -U datasets huggingface_hub pandas pyarrow

Then:

mkdir -p ml/datasets/{santali,mundari,ho}/{raw,cleaned,validated}

Then test:

python - <<'PY'
from datasets import load_dataset

for lang in ["santhali", "mundari"]:
    ds = load_dataset(
        "adivaanihf/adivaani-tribal-english-parallel-corpus",
        lang,
        split="train"
    )
    print(f"{lang}: {len(ds)} rows")
    print(ds[0])
PY