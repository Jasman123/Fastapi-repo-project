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

        initial_state = {
            "messages": [],
            "topic": topic,
            "search_queries": [],
            "queries_done": 0,
            "raw_results": [],
            "structured_data" : [],
            "sythesis": "",
            "report_markdown": "",
            "error": None,
        }

        with Timer() as timer:
            try:
                final_state = await research_graph.ainvoke(initial_state)
            except Exception as exc:
                logger.error(f"[{job_id}] Graph execution error: {exc}", exc_info=True)
                record = await self._persit(
                    job_id=job_id,
                    topic=topic,
                    status="failed",
                    report_markdown="",
                    search_queries=[],
                    structured_data=[],
                    elapsed=timer.elapsed,
                    error=str(exc),
                )
        
        if final_state.get("error"):
            record = await self._persit(
                job_id=job_id,
                topic=topic,
                status="failed",
                report_markdown="",
                search_queries=final_state("search_queries", []),
                structured_data=[],
                elapsed=timer.elapsed,
                error=final_state["error"],
            )

        record = await self._persit(
            job_id=job_id,
            topoic=topic,
            status="completed",
            report_markdown=final_state.get("report_markdown", ""),
            search_queries=final_state.get("search_queries", []),
            structured_data=final_state.get("structured_data", []),
            elapsed=timer.elapsed,
        )
        logger.info(f"[{job_id}] Completed in {timer.elapsed}")
        return record
    
    async def get_report(self, job_id: str) -> ReportRecord:
        stmt = select(ReportModel).where(ReportModel.job_id == job_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()

        if row is None:
            raise ReportNotFoundError(f"Report {job_id!r} not found")
        
        return self._to_record(row)
    
    async def list_report(self, limit: int = 20) -> list[ReportRecord]:
        stmt = (
            select(ReportModel). order_by(ReportModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_record(r) for r in result.scalar().all()]
    
    async def _persist(
            self, *,
            job_id: str, topic: str, status: str, report_markdown: str, search_queries: list[str],
            structured_data: list[dict], elapsed: float, error: str | None = None,
    ) -> ReportRecord:
        sources = [
            SourceRecord(
                title = d.get("title", ""),
                url=d.get("source", ""),
                key_points = d.get("key_points", []),
                relevance_score = d.get("relevance_score", 0.0),
            )
            for d in structured_data
        ]
        row = ReportModel(
            job_id=job_id, topic=topic, status=status, report_markdown=report_markdown, search_queries_json=json.dumps(search_queries),
            sources_json=json.dumps([{

                "title" : s.title,
                "url": s.url,
                "key_points": s.key_points,
                "relevance_score": s.relevance_score,

            }

            for s in sources
                
            ]),
            sources_count=len(sources),
            elapsed_seconds=elapsed,
            error_message=error,
            created_at=datetime.utcnow(),

        )
        self._session.add(row)
        await self._session.flush()

        return ReportRecord(
            job_id=job_id,
            topic=topic,
            status=status,
            report_markdown=report_markdown,
            search_queries=search_queries,
            sources=sources,
            elapsed_seconds=elapsed,
            error_message=error,
            created_at=row.created_at,
        )
    
    @staticmethod
    def _to_record(row: ReportModel) -> ReportRecord:
        sources = [
            SourceRecord(
                title=s.get("title", ""),
                url=s.get("url", ""),
                key_points=s.get("key_points", []),
                relevance_score=s.get("relevance_score", 0.0),
            )
            for s in row.sources
        ]

        return ReportRecord(
            job_id=row.job_id,
            topic=row.topic,
            status=row.status,
            report_markdown=row.report_markdown,
            search_queries=row.search_queries,
            sources=sources,
            elapsed_seconds=row.elapsed_seconds,
            error_message=row.error_message,
            created_at=row.created_at,
        )