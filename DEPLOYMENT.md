# BHASHA SETU - Deployment & Production Guide

## Overview

BHASHA SETU is a production-ready multilingual education AI platform built with FastAPI, SQLAlchemy, and modern Python best practices. This guide covers deployment, scaling, and production operations.

## Quick Start (Development)

```bash
# Clone and setup
cd application
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload

# Access
- Dashboard: http://localhost:8000/
- Admin: http://localhost:8000/admin
- API Docs: http://localhost:8000/docs
```

## Database Setup

### Development
- **Type**: SQLite (file-based)
- **Location**: `application/bhasha_setu.db`
- **Created automatically** on first startup via `init_db()` in app/models.py
- **Tables**: 3 tables with relationships
  - `dataset_entries` - Translation pairs (rows: source_language, target_language, domain, source_text, target_text, validated)
  - `glossary_terms` - Language vocabulary (rows: language_code, english_term, native_term, domain, definition)
  - `language_packs` - Language model metadata (rows: code, name, maturity, model_version, glossary_count)

### Production (PostgreSQL)
```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# Update DATABASE_URL in app/models.py
DATABASE_URL = "postgresql://user:password@localhost:5432/bhasha_setu"

# Run migrations with Alembic
alembic upgrade head
```

## Running Tests

```bash
# All tests (12 total)
pytest

# Individual test suites
pytest tests/test_api.py          # Core API (4 tests)
pytest tests/test_dataset_admin.py  # Database (2 tests)
pytest tests/test_glossary.py     # Vocabulary system (6 tests)

# With coverage
pytest --cov=app
```

## Deployment Options

### Option 1: Docker (Recommended for Production)

```dockerfile
# Build
docker build -t bhasha-setu:1.0.0 .

# Run with SQLite (development-like)
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  bhasha-setu:1.0.0

# Run with PostgreSQL (production)
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  bhasha-setu:1.0.0
```

### Option 2: Cloud Platforms

**Google Cloud Run**
```bash
gcloud run deploy bhasha-setu \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**AWS Lambda with Mangum**
```bash
pip install mangum
# Update main.py to use Mangum for Lambda
```

**Railway / Render**
- Connect your GitHub repository
- Set environment variables
- Deploy automatically on push

### Option 3: Traditional Server (Nginx + Gunicorn)

```bash
# Install production server
pip install gunicorn

# Run with Gunicorn (4 workers)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 main:app

# Nginx reverse proxy configuration
server {
    listen 80;
    server_name api.bhasha-setu.local;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Environment Variables

Create `.env` file:
```bash
# App config
APP_NAME=BHASHA SETU
ENVIRONMENT=production
ALLOWED_ORIGINS=["https://bhasha-setu.local", "https://api.bhasha-setu.local"]

# Database
DATABASE_URL=sqlite:///./bhasha_setu.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@host:5432/bhasha_setu

# Optional: ML model paths
INDICTR ANS_MODEL_PATH=/models/indictr ans2.onnx
ASR_MODEL_PATH=/models/asr_santali.onnx
TTS_MODEL_PATH=/models/tts_santali.onnx
```

## API Endpoints Reference

### Core Endpoints
- `GET /api/health` - System status
- `GET /api/languages` - Language registry  
- `POST /api/translate` - Translation (education-aware)
- `GET /api/language-packs` - Language pack metadata

### Dataset Management (Admin)
- `POST /api/dataset/entries` - Add validated translation pair
- `GET /api/dataset/entries` - List all entries
- `GET /api/dataset/stats` - Aggregated statistics

### Glossary/Vocabulary
- `POST /api/glossary/terms` - Add vocabulary term
- `GET /api/glossary/terms` - List terms (supports filtering)
  - `?language_code=sat` - Filter by language
  - `?domain=fln` - Filter by domain (fln, mathematics, education, etc.)
  - `?language_code=sat&domain=fln` - Combined filters

## Scaling Strategies

### Horizontal Scaling
1. **Load Balancer** (Nginx, HAProxy)
   - Route requests across multiple app instances
   - SSL/TLS termination
   
2. **Database Replication** (PostgreSQL)
   - Primary-replica setup
   - Read replicas for analytics queries

3. **Caching Layer** (Redis)
   ```python
   # Add to app/services.py
   from redis import Redis
   redis = Redis(host='localhost', port=6379)
   ```

4. **Message Queue** (Celery + RabbitMQ)
   - Async dataset processing
   - Background ML model inference

### Vertical Scaling
- Increase server resources (CPU, memory, disk)
- Use PostgreSQL connection pooling (pgBouncer)
- Enable GZIP compression in middleware

## Monitoring & Logging

### Application Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### Health Checks
```bash
# Monitor app health
curl http://localhost:8000/api/health
```

### Metrics (Prometheus Integration)
```bash
pip install prometheus-client

# Exposed at /metrics endpoint
```

### Error Tracking
```bash
# Add Sentry integration
pip install sentry-sdk
```

## Security Checklist

- [ ] Use HTTPS in production (let's Encrypt)
- [ ] Set secure CORS origins only
- [ ] Enable CSRF protection for admin endpoints
- [ ] Rate limiting on public API
- [ ] Database connection encryption
- [ ] Input validation (Pydantic handles this)
- [ ] SQL injection prevention (SQLAlchemy ORM prevents this)
- [ ] Secure secret management (.env files, vault)
- [ ] API authentication (add JWT if needed)
- [ ] Regular database backups

## Backup & Recovery

### SQLite Backup
```bash
# Simple file copy
cp bhasha_setu.db bhasha_setu.db.backup

# Scheduled backup
0 2 * * * cp /app/bhasha_setu.db /backups/bhasha_setu.db.$(date +\%Y\%m\%d)
```

### PostgreSQL Backup
```bash
# Full backup
pg_dump -U user bhasha_setu > backup.sql

# Restore
psql -U user bhasha_setu < backup.sql
```

## Performance Tuning

### Database Optimization
```python
# Add indexes for common queries
# In models.py - add to table definitions:
# index=True on frequently searched columns

# Example:
source_language = Column(String(10), index=True)
target_language = Column(String(10), index=True)
domain = Column(String(50), index=True)
```

### Query Optimization
```python
# Use lazy loading for relationships
from sqlalchemy.orm import selectinload

# Batch operations
db.add_all(entries)  # Instead of multiple add() calls
db.commit()
```

### Caching Strategies
- Cache language metadata (rarely changes)
- Cache language pack info
- Use ETags for API responses

## Maintenance

### Scheduled Tasks
```bash
# Daily: Clean old test data
0 1 * * * sqlite3 /app/bhasha_setu.db "DELETE FROM dataset_entries WHERE validated = false AND DATE(created_at) < DATE('now', '-30 days')"

# Weekly: Database integrity check
0 3 * * 0 sqlite3 /app/bhasha_setu.db "PRAGMA integrity_check"

# Monthly: Backup
0 0 1 * * tar -czf /backups/app-$(date +\%Y\%m\%d).tar.gz /app
```

### Version Updates
```bash
# Update dependencies safely
pip install --upgrade -r requirements.txt
pytest  # Verify all tests still pass
# Stage changes in version control
# Test in staging environment
# Deploy to production
```

## Troubleshooting

### Database Locked Error
```bash
# SQLite issue - check for concurrent writes
# Solution: Use WAL mode
# In app/models.py, add:
from sqlalchemy import event
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
```

### Memory Leaks
```bash
# Monitor with
top -p $(pgrep -f uvicorn)

# Or use memory profiler
pip install memory-profiler
python -m memory_profiler app/main.py
```

### Slow Queries
```python
# Enable SQLAlchemy echo in development
engine = create_engine(DATABASE_URL, echo=True)

# Use query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## Next Steps for ML Integration

1. **Add IndicTrans2 Model** (Santali)
   ```python
   # In app/services.py
   from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
   model = AutoModelForSeq2SeqLM.from_pretrained("...")
   ```

2. **Add ASR/TTS** (Speech)
   ```python
   # Audio endpoints in app/routes.py
   @api_router.post("/api/transcribe")
   def transcribe_audio(file: UploadFile):
       # Use Whisper or similar
       pass
   ```

3. **Dataset Pipeline** (Model Training)
   ```python
   # Bulk import CSV
   # Model fine-tuning on validated data
   # Evaluation metrics tracking
   ```

## Support & Contribution

For issues and feature requests:
1. Check existing GitHub issues
2. Review documentation
3. Submit detailed bug reports with logs
4. Propose features with use cases

## License

[Add your license here]

---

**Last Updated**: September 2, 2026  
**Current Version**: 1.0.0  
**Status**: Production Ready ✅
