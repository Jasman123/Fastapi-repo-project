import logging

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AuthDep, ServiceDep
from app.core.exceptions import ReportNotFoundError, ResearchAgentError
from app.schemas.research import (
    ReportListItem,
    ResearchRequest,
    ResearchResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/research", tags=["research"])


@router.post(
    "",
    response_model=ResearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Run a full research pipeline and return a Markdown report",
)
async def run_research(
    request: ResearchRequest,
    _: AuthDep,
    svc: ServiceDep,
) -> ResearchResponse:
    """
    Triggers the 5-node LangGraph pipeline:
      plan → search (loop) → extract → synthesize → report

    Returns the complete Markdown report synchronously.
    """
    try:
        record = await svc.run_research(request.topic)
    except ResearchAgentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    return ResearchResponse(
        job_id=record.job_id,
        topic=record.topic,
        status=record.status,
        report_markdown=record.report_markdown,
        search_queries=record.search_queries,
        sources_count=len(record.sources),
        elapsed_seconds=record.elapsed_seconds,
        created_at=record.created_at,
    )


@router.get(
    "/{job_id}",
    response_model=ResearchResponse,
    summary="Retrieve a previously generated report by job ID",
)
async def get_report(
    job_id: str,
    _: AuthDep,
    svc: ServiceDep,
) -> ResearchResponse:
    try:
        record = await svc.get_report(job_id)
    except ReportNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{job_id}' not found",
        )

    return ResearchResponse(
        job_id=record.job_id,
        topic=record.topic,
        status=record.status,
        report_markdown=record.report_markdown,
        search_queries=record.search_queries,
        sources_count=len(record.sources),
        elapsed_seconds=record.elapsed_seconds,
        created_at=record.created_at,
    )


@router.get(
    "",
    response_model=list[ReportListItem],
    summary="List recent research reports",
)
async def list_reports(
    _: AuthDep,
    svc: ServiceDep,
    limit: int = 20,
) -> list[ReportListItem]:
    records = await svc.list_reports(limit=limit)
    return [
        ReportListItem(
            job_id=r.job_id,
            topic=r.topic,
            status=r.status,
            sources_count=len(r.sources),
            elapsed_seconds=r.elapsed_seconds,
            created_at=r.created_at,
        )
        for r in records
    ]