"""
Pydantic v2 schemas — single source of truth for request / response shapes.
FastAPI uses these for automatic OpenAPI docs and input validation.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── Enumerations ──────────────────────────────────────────────────────────────

class TicketCategory(str, Enum):
    BILLING      = "billing"
    TECHNICAL    = "technical"
    ACCOUNT      = "account"
    GENERAL      = "general"
    ESCALATION   = "escalation"   # assigned by the agent, not the user


class TicketPriority(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"
    URGENT = "urgent"


class AgentAction(str, Enum):
    ANSWER    = "answer"     # resolved by AI
    ESCALATE  = "escalate"   # routed to human
    CLARIFY   = "clarify"    # agent asked follow-up


# ── Request schemas ───────────────────────────────────────────────────────────

class SupportTicket(BaseModel):
    """Inbound customer support request."""

    ticket_id: str = Field(..., description="Unique ticket reference", examples=["TKT-001"])
    customer_name: str = Field(..., min_length=1, max_length=120)
    message: str = Field(..., min_length=5, max_length=4000, description="Customer's message")
    category_hint: Optional[TicketCategory] = Field(
        None, description="Optional pre-classification from the frontend"
    )
    priority: TicketPriority = TicketPriority.MEDIUM

    @field_validator("message")
    @classmethod
    def no_empty_message(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message cannot be blank")
        return v.strip()


# ── Internal state (flows through the LangGraph pipeline) ─────────────────────

class AgentState(BaseModel):
    """Mutable state threaded through every LangGraph node."""

    ticket: SupportTicket
    category: Optional[TicketCategory] = None
    confidence: float = 0.0          # classifier confidence [0, 1]
    draft_answer: Optional[str] = None
    final_answer: Optional[str] = None
    action: Optional[AgentAction] = None
    escalation_reason: Optional[str] = None
    node_trace: list[str] = Field(default_factory=list)   # for debug / audit


# ── Response schemas ──────────────────────────────────────────────────────────

class SupportResponse(BaseModel):
    """What the API returns to the caller."""

    ticket_id: str
    action: AgentAction
    category: TicketCategory
    confidence: float = Field(..., ge=0.0, le=1.0)
    answer: Optional[str] = None
    escalation_reason: Optional[str] = None
    node_trace: list[str]              # shows the graph path taken — great for demos
    processing_time_ms: float


class BatchResponse(BaseModel):
    results: list[SupportResponse]
    total: int
    resolved: int
    escalated: int
    avg_confidence: float
