from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.models import init_db
from app.routes import api_router

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATE_DIR = BASE_DIR / "app" / "templates"

app = FastAPI(
    title="BHASHA SETU",
    version="1.0.0",
    description=(
        "Production-ready education-focused translation and language orchestration platform "
        "for Santali, Mundari, and Ho."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(api_router, prefix="/api")

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "BHASHA SETU",
            "subtitle": "Education-aware low-resource language AI system",
            "languages": [
                {"code": "sat", "name": "Santali", "maturity": "Production"},
                {"code": "mun", "name": "Mundari", "maturity": "Prototype"},
                {"code": "ho", "name": "Ho", "maturity": "Prototype"},
            ],
        },
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "title": "BHASHA SETU Admin",
            "subtitle": "Native-language validation and dataset operations",
        },
    )
