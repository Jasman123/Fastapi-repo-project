import json
import logging 
from typing import Any

from langchain_core.messages import AImessage
from langchain_core.prompts import ChatPromptTemplate


from app.tools.llm import get_llm
from app.tools.search import web_search


logger = logging.getLogger(__name__)


async def plan_research(state: dict) -> dict:
    topic = state["topic"]
    llm = get_llm()


    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a research planner. Given a research topic, generate exactly 4 "
            "focused search queries that together cover: background, recent developments, "
            "key players, and future outlook. "
            "Respond ONLY with a JSON array of strings. No explanation, no markdown fences."
        )),
        ("human", "Research topic: {topic}"),
    ])

    chain = prompt | llm

    try :
        response = await chain.ainvoke({"topic" : topic})
        raw = response.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        queries = json.load(raw)
        logger.info(f"Planned {len(queries)} queries for {topic}")

        return {
            "search_queries" : queries,
            "queries_done" : 0,
            "message": [AImessage(content = f"Researh plan ready : {len(queries)} queries")],
        }
    
    except Exception as e:
        logger.erro(f"plan_research failed: {e}")
        return {"error": str(e), "search_queries": [], "queries_done": 0 }


