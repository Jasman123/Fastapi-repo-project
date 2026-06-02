from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router


import os


import logging

settings = get_settings()
setup_logging(level=settings.log_level)

logger = logging.getLogger(__name__)
logger.info(f"Starting {settings.app_name} with log level {settings.app_env}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.chroma_persits_dir, exist_ok=True)

    yield

    logger.info("Shutting down application...")

app = FastAPI(
    title=settings.app_name,
    description="Production RAG API with Langgraph + PDF support",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],  # CORS hanya diizinkan di dev
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
async def health():
    return{
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
    }