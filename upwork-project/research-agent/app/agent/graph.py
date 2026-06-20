import logging

from langgraph.graph import END, StateGraph

from app.agent.nodes import extract_data, generate_report, plan_research, search_web, synthesize
from app.agent.state import AgentState


logger = logging.getLogger(__name__)

def _route_after_search(state: AgentState) -> str:
    if state.get("error"):
        logger.warning(f"Error flag set - routing to END: {state['error']}")
        return END

    done = state.get("queries_done", 0)
    total = len(state.get("search_queries", []))

    if done < total:
        return "search_web"

    return "extract_data"

def build_graph() -> StateGraph:
    g = StateGraph(AgentState)

    g.add_node("plan_research", plan_research)
    g.add_node("search_web", search_web)
    g.add_node("extract_data", extract_data)
    g.add_node("synthesize", synthesize)
    g.add_node("generate_report", generate_report)

    g.set_entry_point("plan_research")

    branch = {
        "search_web": "search_web",
        "extract_data": "extract_data",
        END: END,
    }

    g.add_edge("plan_research", "search_web")
    g.add_conditional_edges("search_web", _route_after_search, branch)

    g.add_edge("extract_data",    "synthesize")
    g.add_edge("synthesize",      "generate_report")
    g.add_edge("generate_report", END)

    return g.compile()

research_graph = build_graph()
