"""
LangGraph Multi-Agent Pipeline
═══════════════════════════════
Graph topology:

  [START]
     │
     ▼
  classify_ticket          ← Node 1: determine category + confidence
     │
     ├─ confidence < threshold ──► escalate_ticket   ← Node 3: human hand-off
     │
     └─ confidence ≥ threshold ──► generate_answer   ← Node 2: draft AI reply
                                        │
                                        ▼
                                   review_answer      ← Node 4: quality gate
                                        │
                                   ┌───┴───────┐
                               ok  │           │ poor
                                   ▼           ▼
                                [END]    escalate_ticket

Each node receives and returns AgentState — LangGraph handles routing.
"""

import json
import logging
import re
import time
from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.models.schemas import (
    AgentAction,
    AgentState,
    SupportResponse,
    SupportTicket,
    TicketCategory,
)
from app.services.llm_service import get_llm_response

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Helper: call LLM and parse JSON safely
# ─────────────────────────────────────────────────────────────────────────────

def _parse_json_from_llm(raw: str) -> dict:
    """Strip markdown fences and parse JSON from LLM output."""
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    return json.loads(cleaned)


# ─────────────────────────────────────────────────────────────────────────────
# Node 1 — Classify
# ─────────────────────────────────────────────────────────────────────────────

def classify_ticket(state: AgentState) -> AgentState:
    """
    Sends the ticket to the LLM and gets back:
      { "category": "...", "confidence": 0.87 }
    Updates state.category and state.confidence.
    """
    state.node_trace.append("classify_ticket")
    logger.info(f"[{state.ticket.ticket_id}] Classifying …")

    prompt = f"""You are a support ticket classifier.

Ticket message: "{state.ticket.message}"

Respond with ONLY a JSON object (no extra text):
{{
  "category": "<one of: billing, technical, account, general>",
  "confidence": <float between 0 and 1>
}}"""

    raw = get_llm_response(prompt)

    try:
        parsed = _parse_json_from_llm(raw)
        state.category   = TicketCategory(parsed["category"])
        state.confidence = float(parsed["confidence"])
    except Exception as exc:
        logger.warning(f"[{state.ticket.ticket_id}] Classification parse failed: {exc}. Defaulting to general/low.")
        state.category   = TicketCategory.GENERAL
        state.confidence = 0.4   # force escalation path

    logger.info(f"[{state.ticket.ticket_id}] → {state.category} (conf={state.confidence:.2f})")
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Node 2 — Generate Answer
# ─────────────────────────────────────────────────────────────────────────────

def generate_answer(state: AgentState) -> AgentState:
    """
    Given the category, drafts a helpful, on-brand support reply.
    """
    state.node_trace.append("generate_answer")
    logger.info(f"[{state.ticket.ticket_id}] Generating answer …")

    prompt = f"""You are a friendly, professional customer support agent.

Customer name: {state.ticket.customer_name}
Ticket category: {state.category}
Customer message: "{state.ticket.message}"

Write a clear, helpful reply (2–4 sentences). Be warm but concise.
Do NOT make up specific account data or prices.
"""

    state.draft_answer = get_llm_response(prompt)
    logger.info(f"[{state.ticket.ticket_id}] Draft generated ({len(state.draft_answer)} chars)")
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Node 3 — Escalate
# ─────────────────────────────────────────────────────────────────────────────

def escalate_ticket(state: AgentState) -> AgentState:
    """
    Marks the ticket for human review and sets a reason.
    In production this would also send a Slack / PagerDuty alert.
    """
    state.node_trace.append("escalate_ticket")
    logger.info(f"[{state.ticket.ticket_id}] Escalating to human …")

    state.action = AgentAction.ESCALATE

    if state.escalation_reason is None:
        # Called from the classify branch (low confidence)
        state.escalation_reason = (
            f"Classifier confidence too low ({state.confidence:.0%}) "
            f"for category '{state.category}'. Needs human review."
        )

    state.final_answer = None
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Node 4 — Review Answer (quality gate)
# ─────────────────────────────────────────────────────────────────────────────

def review_answer(state: AgentState) -> AgentState:
    """
    A second LLM pass checks whether the draft answer is appropriate.
    Returns { "ok": true/false, "reason": "..." }
    """
    state.node_trace.append("review_answer")
    logger.info(f"[{state.ticket.ticket_id}] Reviewing answer quality …")

    prompt = f"""You are a QA reviewer for customer support replies.

Original question: "{state.ticket.message}"
Proposed answer: "{state.draft_answer}"

Respond with ONLY JSON:
{{
  "ok": <true if the answer is helpful and appropriate, false otherwise>,
  "reason": "<brief reason>"
}}"""

    raw = get_llm_response(prompt)

    try:
        parsed = _parse_json_from_llm(raw)
        if parsed.get("ok", False):
            state.action       = AgentAction.ANSWER
            state.final_answer = state.draft_answer
            logger.info(f"[{state.ticket.ticket_id}] QA passed ✓")
        else:
            # Quality gate failed → escalate
            state.escalation_reason = f"QA review rejected draft: {parsed.get('reason', 'unknown')}"
            logger.warning(f"[{state.ticket.ticket_id}] QA failed — escalating")
    except Exception as exc:
        logger.warning(f"[{state.ticket.ticket_id}] QA parse failed: {exc}. Accepting draft.")
        state.action       = AgentAction.ANSWER
        state.final_answer = state.draft_answer

    return state


# ─────────────────────────────────────────────────────────────────────────────
# Conditional edge — after classify_ticket
# ─────────────────────────────────────────────────────────────────────────────

def route_after_classify(state: AgentState) -> Literal["generate_answer", "escalate_ticket"]:
    if state.confidence >= settings.escalation_confidence_threshold:
        return "generate_answer"
    return "escalate_ticket"


def route_after_review(state: AgentState) -> Literal["END", "escalate_ticket"]:
    if state.action == AgentAction.ANSWER:
        return "END"
    return "escalate_ticket"


# ─────────────────────────────────────────────────────────────────────────────
# Graph assembly
# ─────────────────────────────────────────────────────────────────────────────

def build_graph():
    """
    Assembles and compiles the LangGraph StateGraph.
    Call once at startup; reuse the compiled graph for all requests.
    """
    # LangGraph requires a dict-based state; we wrap our Pydantic model
    graph = StateGraph(dict)

    # Add nodes (each takes state dict, returns updated state dict)
    graph.add_node("classify_ticket",  lambda s: _node_adapter(classify_ticket, s))
    graph.add_node("generate_answer",  lambda s: _node_adapter(generate_answer, s))
    graph.add_node("review_answer",    lambda s: _node_adapter(review_answer, s))
    graph.add_node("escalate_ticket",  lambda s: _node_adapter(escalate_ticket, s))

    # Edges
    graph.add_edge(START, "classify_ticket")
    graph.add_conditional_edges(
        "classify_ticket",
        lambda s: route_after_classify(_dict_to_state(s)),
    )
    graph.add_edge("generate_answer", "review_answer")
    graph.add_conditional_edges(
        "review_answer",
        lambda s: route_after_review(_dict_to_state(s)),
        {"END": END, "escalate_ticket": "escalate_ticket"},
    )
    graph.add_edge("escalate_ticket", END)

    return graph.compile()


# ── Adapters (Pydantic ↔ LangGraph dict) ──────────────────────────────────────

def _state_to_dict(state: AgentState) -> dict:
    return state.model_dump()


def _dict_to_state(d: dict) -> AgentState:
    return AgentState.model_validate(d)


def _node_adapter(fn, state_dict: dict) -> dict:
    """Converts dict → AgentState, runs node, converts back."""
    state = _dict_to_state(state_dict)
    updated = fn(state)
    return _state_to_dict(updated)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

# Compile graph once at import time
_graph = build_graph()


def run_support_agent(ticket: SupportTicket) -> SupportResponse:
    """
    Main entry point used by the FastAPI route.
    Runs the compiled LangGraph and returns a structured response.
    """
    start = time.perf_counter()

    initial_state = AgentState(ticket=ticket)
    final_dict    = _graph.invoke(_state_to_dict(initial_state))
    final_state   = _dict_to_state(final_dict)

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    return SupportResponse(
        ticket_id           = ticket.ticket_id,
        action              = final_state.action or AgentAction.ESCALATE,
        category            = final_state.category or TicketCategory.GENERAL,
        confidence          = final_state.confidence,
        answer              = final_state.final_answer,
        escalation_reason   = final_state.escalation_reason,
        node_trace          = final_state.node_trace,
        processing_time_ms  = elapsed_ms,
    )
