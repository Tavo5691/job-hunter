"""
job-hunter FastAPI application entry point.

Start with:  uv run uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import profiles
from app.services.extractor_factory import is_llm_extractor_enabled

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Developer-focused job hunting assistant — PDF CV upload, profile extraction, gap analysis.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow the Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(profiles.router, prefix="/api/v1")


@app.get("/health", tags=["meta"])
def health_check() -> dict:
    """Simple health-check endpoint used by Docker and monitoring."""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "extractor": "llm" if is_llm_extractor_enabled() else "regex",
    }
