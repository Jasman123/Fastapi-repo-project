"""
Test suite for the AI Support Agent pipeline.
All LLM calls are mocked — tests run offline without an API key.

Run:
    pytest tests/ -v
"""

import pytest
from unittest.mock import patch

from app.agents.support_graph import run_support_agent
from app.models.schemas import (
    AgentAction,
    SupportTicket,
    TicketCategory,
    TicketPriority,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def billing_ticket():
    return SupportTicket(
        ticket_id="TKT-TEST-001",
        customer_name="Alice",
        message="I was charged twice this month. Please refund.",
        priority=TicketPriority.HIGH,
    )


@pytest.fixture
def vague_ticket():
    return SupportTicket(
        ticket_id="TKT-TEST-002",
        customer_name="Bob",
        message="Something went wrong I think.",
        priority=TicketPriority.LOW,
    )


# ── Happy path: billing ticket resolved ───────────────────────────────────────

def test_billing_ticket_resolved(billing_ticket):
    """High-confidence billing ticket should flow: classify → generate → review → ANSWER."""
    mock_responses = iter([
        '{"category": "billing", "confidence": 0.95}',   # classify
        "Hi Alice, we'll refund the duplicate charge within 3–5 business days.",  # generate
        '{"ok": true, "reason": "Clear and helpful."}',   # review
    ])

    with patch("app.agents.support_graph.get_llm_response", side_effect=lambda *a, **k: next(mock_responses)):
        result = run_support_agent(billing_ticket)

    assert result.action   == AgentAction.ANSWER
    assert result.category == TicketCategory.BILLING
    assert result.confidence >= 0.9
    assert result.answer is not None
    assert "classify_ticket"  in result.node_trace
    assert "generate_answer"  in result.node_trace
    assert "review_answer"    in result.node_trace
    assert "escalate_ticket"  not in result.node_trace


# ── Low confidence → escalation ───────────────────────────────────────────────

def test_low_confidence_escalates(vague_ticket):
    """A vague ticket with low classifier confidence should be escalated."""
    mock_responses = iter([
        '{"category": "general", "confidence": 0.30}',   # classify → low conf
    ])

    with patch("app.agents.support_graph.get_llm_response", side_effect=lambda *a, **k: next(mock_responses)):
        result = run_support_agent(vague_ticket)

    assert result.action == AgentAction.ESCALATE
    assert result.answer is None
    assert result.escalation_reason is not None
    assert "escalate_ticket" in result.node_trace
    assert "generate_answer" not in result.node_trace


# ── QA gate failure → escalation ─────────────────────────────────────────────

def test_qa_failure_escalates(billing_ticket):
    """If the QA reviewer rejects the draft, the ticket should escalate."""
    mock_responses = iter([
        '{"category": "billing", "confidence": 0.90}',    # classify
        "Call us at 1-800-FREE-MONEY.",                    # bad draft
        '{"ok": false, "reason": "Inappropriate content."}',  # review rejects
    ])

    with patch("app.agents.support_graph.get_llm_response", side_effect=lambda *a, **k: next(mock_responses)):
        result = run_support_agent(billing_ticket)

    assert result.action == AgentAction.ESCALATE
    assert "escalate_ticket" in result.node_trace


# ── Input validation ──────────────────────────────────────────────────────────

def test_empty_message_raises():
    """Pydantic should reject a blank message."""
    with pytest.raises(Exception):  # pydantic ValidationError
        SupportTicket(ticket_id="X", customer_name="Y", message="   ")


# ── Response shape ────────────────────────────────────────────────────────────

def test_response_shape(billing_ticket):
    """Result must always have ticket_id, action, category, confidence, and node_trace."""
    mock_responses = iter([
        '{"category": "billing", "confidence": 0.88}',
        "We'll sort this out for you, Alice!",
        '{"ok": true, "reason": "Good."}',
    ])

    with patch("app.agents.support_graph.get_llm_response", side_effect=lambda *a, **k: next(mock_responses)):
        result = run_support_agent(billing_ticket)

    assert result.ticket_id  == billing_ticket.ticket_id
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.node_trace, list)
    assert len(result.node_trace) > 0
    assert result.processing_time_ms >= 0
