import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import health, research
from app.core.config import settings
from app.db.database import create_tables
from app.utils.logger import configure_logging

_FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


def create_app() -> FastAPI:
    configure_logging(debug=settings.DEBUG)
    logger = logging.getLogger(__name__)

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="LangGraph-powered automated research and report generation",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup():
        await create_tables()
        logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} ready")

    app.include_router(health.router)
    app.include_router(research.router)

    if _FRONTEND_DIR.is_dir():
        app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")

    return app


app = create_app()