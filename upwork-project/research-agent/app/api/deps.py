import logging
from typing import Annotated


from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthError
from app.db.database import get_session
from app.services.research_services import ResearchService

logger = logging.getLogger(__name__)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(key: Annotated[str | None, Security(_api_key_header)],
                     cfg: Annotated[Settings, Depends(get_settings)],) -> str :
    if not key or key != cfg.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-key header",
        )
    
    return key

async def get_research_service( session: Annotated[AsyncSession, Depends(get_session)],) -> ResearchService:
    return ResearchService(session)

AuthDep = Annotated[str, Depends(verify_api_key)]
ServiceDep = Annotated[ResearchService, Depends(get_research_service)]