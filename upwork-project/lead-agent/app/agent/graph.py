from langgraph.graph  import StateGraph, START, END
from app.agent.state import AgentState
from app.agent.nodes import (
    scrape_node,
    extract_node,
    score_node,
    compose_node,
    deliver_node,
)
from app.core.logging import get_logger
logger = get_logger(__name__)



def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("scrape", scrape_node)
    graph.add_node("extract", extract_node)
    graph.add_node("score", score_node)
    graph.add_node("compose", compose_node)
    graph.add_node("deliver", deliver_node)

    graph.add_edge(START, "scrape")
    graph.add_edge("scrape", "extract")
    graph.add_edge("extract", "score")
    graph.add_edge("score", "compose")
    graph.add_edge("compose", "deliver")
    graph.add_edge("deliver", END)

    compiled = graph.compile()
    logger.info("LangGraph pipeline compiled — 5 nodes ready")
    return compiled

lead_graph = build_graph()