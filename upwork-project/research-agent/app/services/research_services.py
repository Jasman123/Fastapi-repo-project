import json
import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import research_graph
from app.core.exceptions import ReportNotFoundError, ResearchAgentError
from app.db.models import ReportModel
from app.schemas.report import ReportRecord, SourceRecord
from app.utils.timing import Timer


logger = logging.getLogger(__name__)


class ResearchService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def run_research(self, topic: str) -> ReportRecord:
        job_id = str(uuid.uuid4())
        logger.infor(f"[{job_id}] Research started: {topic!r}")