"""CodeGuard AI - FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.database.session import init_db
from app.services.ai import provider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("codeguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.ai_configured:
        logger.info("AI provider configured: %s (%s)", settings.ai_provider or "openai-compatible", settings.ai_model)
    else:
        logger.info("No AI provider configured - running in offline deterministic mode.")
    yield


app = FastAPI(
    title="CodeGuard AI",
    description="AI-powered GitHub code review and bug detection platform.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {"name": settings.app_name, "status": "ok", "docs": "/docs"}


@app.get("/api/health", tags=["meta"])
def health() -> dict:
    return {"status": "healthy", "ai_configured": provider.is_available()}
