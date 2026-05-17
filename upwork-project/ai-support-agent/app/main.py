"""
AI Customer Support Agent — FastAPI entry point.
Exposes REST endpoints consumed by frontend and tests.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import settings

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀  AI Support Agent starting up …")
    yield
    logger.info("🛑  AI Support Agent shutting down.")


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Customer Support Agent",
    description=(
        "Multi-agent pipeline built with LangChain + LangGraph + FastAPI. "
        "Classifies tickets, generates answers, and escalates when needed."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — open for demo; tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request-timing middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(elapsed)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({elapsed} ms)")
    return response


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "version": app.version}


# ── Mount routes ──────────────────────────────────────────────────────────────
app.include_router(router, prefix="/api/v1")
