import asyncio
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

async def web_search(query: str) -> list[dict[str, Any]]:
    if settings.TAVILY_API_KEY:
        return _tavily(query)
    logger.warning("TAVILY_API_KEY not set - using DuckDuckGo fallback")
    return await _ddg(query)

async def _tavily(query: str) -> list[dict[str, Any]]:
    from langchain_community.tools.tavily_search import TavilySearchResults

    tool = TavilySearchResults(
        max_results=settings.MAX_SEARCH_RESULTS,
        tavily_api_key=settings.TAVILY_API_KEY,
        include_answer=False,
        include_raw_content=False,
    )

    results = await tool.ainvoke({"query": query})
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url",""),
            "snippet": r.get("content",""),
        }
        for r in results
    ]

async def _ddg(query: str) -> list[dict[str, Any]]:
    from duckduckgo_search import DDGS

    def _sync():
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=settings.MAX_SEARCH_RESULTS))
        

    results = await asyncio.get_event_loop().run_in_executor(None, _sync)

    return [
        {
            "title" : r.get("title",""),
            "url": r.get("href",""),
            "snippet": r.get("body", ""),
        }
        for r in results
    ]