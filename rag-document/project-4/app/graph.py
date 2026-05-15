from langgraph.graph import StateGraph, END
from .state import GraphState
from .nodes import (
    route_query,
    direct_llm,
    retrieve,
    grade_documents,
    rewrite_query,
    generate,
    grade_answer,
    regenerate,
    route_after_query_classification,
    route_after_grading,
    route_after_answer_grading
)

def build_rag_graph():
    """
    Assembles the complete RAG graph with four conditional edges.

    The graph flow:
    START
     └→ route_query → [direct_llm → grade_answer → END]
                    → [retrieve → grade_documents
                               → [rewrite_query ↩ retrieve]
                               → [generate → grade_answer
                                           → [regenerate → END]
                                           → [END]
                                ]
                    ]
    """

    graph = StateGraph(GraphState)

    graph.add_node('route_query', route_query)
    graph.add_node('direct_llm', direct_llm)
    graph.add_node('retrieve', retrieve)
    graph.add_node('grade_documents', grade_documents)
    graph.add_node('rewrite_query', rewrite_query)
    graph.add_node('generate', generate)
    graph.add_node('grade_answer', grade_answer)
    graph.add_node('regenerate', regenerate)

    graph.set_entry_point('route_query')


    graph.add_conditional_edges(
        'route_query', route_after_query_classification,{'direct_llm': 'direct_llm', 'retrieve':'retrieve',},
    )

    graph.add_edge('retrieve', 'grade_documents')

    graph.add_conditional_edges(
        'grade_documents', route_after_grading, {'rewrite_query': 'rewrite_query', 'generate': 'generate',},
    )

    graph.add_edge('rewrite_query', 'retrieve')
    graph.add_edge('generate', 'grade_answer')

    graph.add_conditional_edges(
        'grade_answer', route_after_answer_grading, {'end': END, 'regenerate': 'regenerate',},
    )

    graph.add_edge('direct_llm', END)
    graph.add_edge('regenerate', END)

    return graph.compile()


rag_graph = build_rag_graph()

