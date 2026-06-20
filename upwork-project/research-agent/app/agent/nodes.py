import json
import logging
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from app.agent.llm import get_llm
from app.agent.search import web_search
from app.core.config import settings
from app.utils.markdown import strip_fences

logger = logging.getLogger(__name__)


async def plan_research(state: dict) -> dict:
    topic = state["topic"]
    n = settings.SEARCH_QUERIES_COUNT
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            f"You are a research planner. Given a topic, produce exactly {n} focused "
            "search queries that together cover: background, recent developments, "
            "key players, and future outlook. "
            "Respond ONLY with a JSON array of strings. No explanation, no fences."
        )),
        ("human", "Research topic: {topic}"),
    ])

    try:
        response = await (prompt | llm).ainvoke({"topic": topic})
        queries: list[str] = json.loads(strip_fences(response.content))
        logger.info(f"Planned {len(queries)} queries for : {topic!r}")

        return {
            "search_queries" : queries,
            "queries_done" : 0,
            "messages": [AIMessage(content=f"Plan ready — {len(queries)} queries")],
        }
    
    except Exception as exc:
        logger.error(f"plan_research failed: {exc}")
        return {
            "error": f"Planning failed: {exc}",
            "search_queries": [],
            "queries_done": 0,
        }
    
async def search_web(state: dict) -> dict:

    idx = state.get("queries_done", 0)
    query = state["search_queries"][idx]
    total = len(state["search_queries"])
    logger.info(f"Search [{idx+1}/{total}]: {query!r}")

    try:
        results = await web_search(query)
        return {
            "raw_results": state.get("raw_results", []) + results,
            "queries_done" : idx + 1,
            "messages": [AIMessage(content=f"Search done: '{query}' -> {len(results)} hits")]
        }
    
    except Exception as exc:
        logger.warning(f"Search failed for '{query} : {exc} - skipping")

        return {
            "queries_done" : idx + 1,
            "messages" : [AIMessage(content=f"Search skipped: '{query}")],
        }

async def extract_data(state: dict) -> dict:

    raw: list[dict[str, Any]] = state.get("raw_results", [])
    if not raw:
        logger.warning("No search results — skipping extraction, report will use LLM knowledge only")
        return {"structured_data": []}
    
    topic = state["topic"]
    llm = get_llm()

    snippet = "\n\n".join(
        f"[{i + 1}] {r.get('title', 'No title')}\n"
        f"URL: {r.get('url', '')}\n"
        f"{r.get('snippet', '')[:300]}"
        for i, r in enumerate(raw[:8])
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a research analyst. Extract structured insights from search results. "
            "Return ONLY a JSON array where each item has: "
            "title (str), source (str), key_points (list[str] max 3), "
            "relevance_score (float 0.0–1.0). No markdown, no explanation."
        )),
        ("human", "Topic: {topic}\n\nSearch results:\n{snippets}"),
    ])

    try:
        response = await (prompt | llm).ainvoke({"topic": topic, "snippets": snippet})
        data: list[dict] = json.loads(strip_fences(response.content))
        data.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        logger.info(f"Extracted {len(data)} structured items")

        return {
            "structured_data" : data,
            "messages": [AIMessage(content=f"Extracted {len(data)} items")],
        }
    
    except Exception as exc:
        logger.warning(f"extract_data failed ({exc}) — continuing without structured data")
        return {"structured_data": []}
    
async def synthesize(state: dict) -> dict:
    data = state.get("structured_data", [])
    topic = state["topic"]
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a senior research analyst. Write a clear, factual 3–4 paragraph "
            "synthesis covering: what is known, what is emerging, key players/forces, "
            "and open questions. Cite sources by title where possible. "
            "Be analytical, not descriptive. Plain prose — no headers, no bullets."
        )),
        ("human", "Topic: {topic}\n\nStructured insights (top 10):\n{data}"),
    ])

    try:
        response = await (prompt | llm).ainvoke({"topic": topic, "data" : json.dumps(data[:10], indent=2),})
        synthesis = response.content.strip()
        logger.info(f"Synthesis: {len(synthesis)} chars")

        return {
            "synthesis": synthesis,
            "messages": [AIMessage(content="Synthesis complete")],
        }
    
    except Exception as exc:
        logger.error(f"synthesize failed: {exc}")
        return {"error" : f"Synthesis failed: {exc}", "synthesis": ""}

async def generate_report(state: dict) -> dict:
    topic = state["topic"]
    synthesis = state.get("synthesis", "")
    data = state.get("structured_data", [])
    queries = state.get("search_queries", [])
    llm = get_llm()

    sources_md = "\n".join(
        f"- [{d.get('title', 'Untitled')}]({d.get('source', '#')})"
        for d in data if d.get("source")
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a professional report writer. Generate a complete, well-structured "
            "Markdown report with these exact sections:\n"
            "# [Title]\n## Executive Summary\n## Background\n"
            "## Key Findings\n## Analysis & Implications\n## Conclusion\n## Sources\n\n"
            "Use proper Markdown. Be professional, concise, and factual. "
            "Do not hallucinate — only use the provided information."
        )),
        ("human", (
            "Topic: {topic}\n\n"
            "Queries used: {queries}\n\n"
            "Executive synthesis:\n{synthesis}\n\n"
            "Findings (top 8):\n{findings}\n\n"
            "Sources:\n{sources}"
        )),
    ])

    try:
        response = await (prompt | llm).ainvoke({
            "topic": topic,
            "queries": ", ".join(queries),
            "synthesis": synthesis,
            "findings": json.dumps(data[:8], indent=2),
            "sources": sources_md[:2000],
        })
        report = response.content.strip()
        logger.info(f"Report generated: {len(report)} chars")
        
        return {
            "report_markdown" : report,
            "messages": [AIMessage(content="Report complete")],
        }
    except Exception as exc:
        logger.error(f"generate_report failed: {exc}")
        return {"error": f"Report generation failed: {exc}", "report_markdown": ""} 


