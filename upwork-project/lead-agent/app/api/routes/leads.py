

from fastapi import APIRouter, HTTPException, status
from app.schemas.lead import LeadInput
from app.schemas.job import BatchJobRequest, BatchJobResponse, SingleLeadResponse
from app.services.lead_service import run_single_lead, run_batch_leads
from app.services.sqlite_services import get_recent_leads
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/leads", tags=["Lead Qualification"])


@router.post(
    "/single",
    response_model=SingleLeadResponse,
    summary="Process a single company URL",
)
async def process_single_lead(payload: LeadInput) -> SingleLeadResponse:
    """
    Runs the full 5-node pipeline for one URL.
    Returns enriched, scored lead with drafted email.
    """
    logger.info(f"Single lead request: {payload.url}")
    try:
        output = await run_single_lead(payload)
        return SingleLeadResponse(
            status="success" if not output.error else "failed",
            output=output,
            error=output.error,
        )
    except Exception as e:
        logger.exception(f"Route error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/batch",
    response_model=BatchJobResponse,
    summary="Process a batch of company URLs",
)
async def process_batch_leads(payload: BatchJobRequest) -> BatchJobResponse:
    """
    Processes up to 50 URLs concurrently.
    Returns aggregated results with hot/warm/cold counts.
    """
    logger.info(f"Batch request: {len(payload.leads)} leads | '{payload.job_label}'")
    try:
        return await run_batch_leads(payload)
    except Exception as e:
        logger.exception(f"Batch route error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/history",
    summary="Get recent processed leads from SQLite",
)
async def get_lead_history(limit: int = 50) -> list[dict]:
    """Returns the most recently processed leads."""
    try:
        return await get_recent_leads(limit=min(limit, 200))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/stats",
    summary="Summary stats for all processed leads",
)
async def get_stats() -> dict:
    """Quick stats — total, hot/warm/cold counts, avg score."""
    try:
        leads = await get_recent_leads(limit=1000)
        if not leads:
            return {"total": 0, "hot": 0, "warm": 0, "cold": 0, "avg_score": 0}

        total = len(leads)
        hot   = sum(1 for l in leads if l["tier"] == "hot")
        warm  = sum(1 for l in leads if l["tier"] == "warm")
        cold  = sum(1 for l in leads if l["tier"] == "cold")
        avg   = round(sum(l["score"] for l in leads) / total, 1)

        return {
            "total": total,
            "hot": hot,
            "warm": warm,
            "cold": cold,
            "avg_score": avg,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))