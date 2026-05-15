from langgraph.graph import StateGraph, END
from .state import GraphState
from .nodes import (
    retrieve,
    grade_document,
    web_search_node,
    generate,
    route_after_grading
)

def build_rag_graph():
    graph = StateGraph(GraphState)

    graph.add_node("retrieve", retrieve)
    graph.add_node("grade_document", grade_document)
    graph.add_node("web_search_node", web_search_node)
    graph.add_node("generate", generate)


    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "grade_document")
    graph.add_edge("web_search_node", "generate")
    graph.add_edge("generate", END)

    graph.add_conditional_edges(
        "grade_document", route_after_grading,
        {
            "generate": "generate",
            "web_search": "web_search_node",
        }
    )

    return graph.compile()

rag_graph = build_rag_graph()