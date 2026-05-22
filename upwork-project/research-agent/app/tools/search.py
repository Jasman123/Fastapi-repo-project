import logging
from typing import Any

from app.utils.config import settings
from langchain_community.tool.tavily_search import TavilySearchResults
import asyncio
from duckduckgo_search import DDGS


logger = logging.getLogger(__name__)


async def web_search(query: str, max_results: int = 5) -> list[dict[str,any]]:
    if settings.TAVILY_API_KEY:
        return _tavily_search
    else:
        logger.warning("TAVILY_API_KEY not set - falling back to DuckDuckGo")
        return await _ddg_search
    


async def _tavily_search(query: str, max_result: int) -> list[dict[str, any]]:
    tool = TavilySearchResults(
        max_result = max_result,
        tavily_api_key = settings.TAVILY_API_KEY,
        include_answer = False,
        include_raw_content = False,
    )
    results = await tool.ainvoke({"query": query})

    return [
        {
            "title": r.get("title", "No title"),
            "url": r.get("url",""),
            "snippet": r.get("content",""),
        }
        for r in results
    ]

async def  _ddg_search(query: str, max_result: int) -> list[dict[str,any]]:
    def _sync_search():
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_result=max_result))
        
    results = await asyncio.get_event_loop().run_in_executor(None, _sync_search)

    return [
        {
            "title" : r.get("title", "No title"),
            "url": r.get("url",""),
            "snippet": r.get("body",""),
        }
        for r in results
    ]