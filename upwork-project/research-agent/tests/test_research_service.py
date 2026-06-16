"""
Service-layer tests — fully mocked, no real API or DB calls.
Tests the service contract: input topic → ReportRecord with correct shape.

Run: pytest tests/ -v
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_mock_session() -> AsyncSession:
    session = MagicMock(spec=AsyncSession)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


MOCK_FINAL_STATE = {
    "topic": "AI agents in enterprise",
    "search_queries": ["AI agents market 2025", "enterprise AI adoption", "LangGraph use cases", "AI automation ROI"],
    "raw_results": [{"title": "Test", "url": "https://example.com", "snippet": "AI agents are..."}],
    "structured_data": [
        {"title": "AI Market Report", "source": "https://example.com", "key_points": ["43% CAGR"], "relevance_score": 0.95}
    ],
    "synthesis": "AI agents are rapidly maturing...",
    "report_markdown": "# AI Agents Report\n\n## Executive Summary\n\nTest content.",
    "error": None,
    "messages": [],
    "queries_done": 4,
}


# ── Service tests ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_research_returns_record():
    """Successful run returns a populated ReportRecord."""
    from app.services.research_services import ResearchService

    session = make_mock_session()

    # Mock the ORM row that gets written
    mock_row = MagicMock()
    mock_row.job_id = "test-job-id"
    mock_row.created_at = datetime.utcnow()

    with patch("app.services.research_services.research_graph") as mock_graph:
        mock_graph.ainvoke = AsyncMock(return_value=MOCK_FINAL_STATE)

        svc = ResearchService(session)
        record = await svc.run_research("AI agents in enterprise")

    assert record.status == "completed"
    assert record.report_markdown == MOCK_FINAL_STATE["report_markdown"]
    assert record.search_queries == MOCK_FINAL_STATE["search_queries"]
    assert len(record.sources) == 1
    assert record.sources[0].relevance_score == 0.95


@pytest.mark.asyncio
async def test_run_research_handles_agent_error():
    """Agent error flag triggers ResearchAgentError, persists failed record."""
    from app.core.exceptions import ResearchAgentError
    from app.services.research_services import ResearchService

    error_state = {**MOCK_FINAL_STATE, "error": "LLM timeout", "report_markdown": ""}
    session = make_mock_session()

    with patch("app.services.research_services.research_graph") as mock_graph:
        mock_graph.ainvoke = AsyncMock(return_value=error_state)

        svc = ResearchService(session)
        with pytest.raises(ResearchAgentError, match="LLM timeout"):
            await svc.run_research("test topic")


@pytest.mark.asyncio
async def test_get_report_not_found():
    """get_report raises ReportNotFoundError for unknown job_id."""
    from app.core.exceptions import ReportNotFoundError
    from app.services.research_services import ResearchService

    session = make_mock_session()
    # Return empty result set
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=mock_result)

    svc = ResearchService(session)
    with pytest.raises(ReportNotFoundError):
        await svc.get_report("nonexistent-id")


# ── Agent node tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_plan_research_parses_queries():
    """plan_research should call LLM and return parsed query list."""
    from app.agent.nodes import plan_research

    mock_response = MagicMock()
    mock_response.content = '["query 1", "query 2", "query 3", "query 4"]'

    mock_chain = AsyncMock(return_value=mock_response)

    with patch("app.agent.nodes.get_llm") as mock_llm:
        with patch("app.agent.nodes.ChatPromptTemplate") as mock_pt:
            mock_prompt = MagicMock()
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)
            mock_pt.from_messages.return_value = mock_prompt

            result = await plan_research({"topic": "AI agents"})

    assert result["queries_done"] == 0
    assert len(result["search_queries"]) == 4


@pytest.mark.asyncio
async def test_search_web_increments_cursor():
    """search_web advances queries_done by 1 per call."""
    from app.agent.nodes import search_web

    state = {
        "search_queries": ["q1", "q2", "q3", "q4"],
        "queries_done": 0,
        "raw_results": [],
    }

    with patch("app.agent.nodes.web_search", AsyncMock(return_value=[
        {"title": "T", "url": "https://x.com", "snippet": "snippet"}
    ])):
        result = await search_web(state)

    assert result["queries_done"] == 1
    assert len(result["raw_results"]) == 1


def test_router_continues_searching():
    """Router returns 'search_web' while queries remain."""
    from app.agent.graph import _route_after_search

    state = {"search_queries": ["q1", "q2", "q3", "q4"], "queries_done": 2, "error": None}
    assert _route_after_search(state) == "search_web"


def test_router_moves_to_extraction():
    """Router returns 'extract_data' when all queries exhausted."""
    from app.agent.graph import _route_after_search

    state = {"search_queries": ["q1", "q2", "q3", "q4"], "queries_done": 4, "error": None}
    assert _route_after_search(state) == "extract_data"


def test_router_ends_on_error():
    """Router returns END when error flag is set."""
    from langgraph.graph import END
    from app.agent.graph import _route_after_search

    state = {"search_queries": ["q1"], "queries_done": 0, "error": "boom"}
    assert _route_after_search(state) == END