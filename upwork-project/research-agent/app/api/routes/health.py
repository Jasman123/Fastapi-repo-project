import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.schemas.research import HealthReponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthReponse, tags=["ops"])
async def health(session: AsyncSession = Depends(get_session)):
    db_status = "error"
    try:
        await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        logger.warning(f"DB health check failed: {exc}")

    from app.core.config import settings
    return HealthReponse(
        status="ok",
        version=settings.APP_VERSION,
        db=db_status,
    )