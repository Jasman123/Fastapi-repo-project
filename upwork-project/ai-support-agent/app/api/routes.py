"""
API Routes — v1
"""

import time
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.agents.support_graph import run_support_agent
from app.models.schemas import (
    BatchResponse,
    SupportResponse,
    SupportTicket,
)

router = APIRouter(tags=["Support Agent"])


@router.post(
    "/tickets",
    response_model=SupportResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a single support ticket",
)
async def process_ticket(ticket: SupportTicket) -> SupportResponse:
    """
    Runs the full LangGraph pipeline for one ticket.
    Returns the AI-generated answer or escalation details.
    """
    try:
        return run_support_agent(ticket)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent error: {exc}",
        )


@router.post(
    "/tickets/batch",
    response_model=BatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Process multiple tickets in one call",
)
async def process_batch(tickets: list[SupportTicket]) -> BatchResponse:
    """
    Processes up to 20 tickets sequentially (parallel batching is a paid-tier feature).
    Great for portfolio demo — shows aggregate stats.
    """
    if len(tickets) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size limited to 20 tickets.",
        )

    results = [run_support_agent(t) for t in tickets]

    resolved  = sum(1 for r in results if r.action.value == "answer")
    escalated = len(results) - resolved
    avg_conf  = round(sum(r.confidence for r in results) / len(results), 3) if results else 0.0

    return BatchResponse(
        results       = results,
        total         = len(results),
        resolved      = resolved,
        escalated     = escalated,
        avg_confidence= avg_conf,
    )
