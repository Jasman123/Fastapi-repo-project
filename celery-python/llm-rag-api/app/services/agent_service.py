import logging
from functools import lru_cache
from operator import add
from typing import Annotated, TypedDict


from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph


from app.core.config import get_settings
from app.db.chroma import VectorStoreRepository
from app.models.schemas import AgentQueryResponse, AgentStep, SourceChunk


logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    question: str
    original_question: str
    documents: list[Document]
    is_relevant: bool 
    answer: str
    iterations: int
    max_iterations: int
    steps: Annotated[list[AgentStep], add]  


def _get_llm(temperature: float = 0.0) -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        api_key = settings.openai_api_key,
        model = settings.chat_model,
        temperature = temperature,
    )

def retrieve_node(state: AgentState) -> dict:
    settings = get_settings()
    repo = VectorStoreRepository()

    results = repo.similarity_search(
        query = state["question"],
        k = settings.top_k,
    )

    documents = [doc for doc, _ in results]
    logger.info(f"[Agent] Retrieved {len(documents)} docs")
    return {
        "documents": documents,
        "steps": [AgentStep(
            step="retrieve",
            output=f"Retrieved {len(documents)} chunks for: '{state['question'][:60]}'"
        )],
    }

def grade_node(state: AgentState) -> dict:
    documents = state["documents"]

    if not documents:
        return {
            "is_relevant": False,
            "steps": [AgentStep(step="grade", output="No documents — not relevant")],
        }
    
    context = "\n\n".join(doc.page_content for doc in documents)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Grade if retrieved documents are relevant to the question.
Respond ONLY with valid JSON: {{"relevant": "yes"}} or {{"relevant": "no"}}"""),
        ("user", "Documents:\n{context}\n\nQuestion: {question}"),
    ])

    chain = prompt | _get_llm() | JsonOutputParser()

    try:
        result = chain.invoke({
            "context": context[:3000],  # Limit context untuk grader
            "question": state["question"],
        })
        is_relevant = result.get("relevant", "no").lower() == "yes"
    except Exception as e:
        logger.warning(f"[Agent] Grading error: {e}, defaulting to relevant")
        is_relevant = True

    return {
        "is_relevant": is_relevant,
        "steps": [AgentStep(
            step="grade",
            output=f"Relevance: {'RELEVANT' if is_relevant else 'NOT RELEVANT'}"
        )],
    }


def rewrite_node(state: AgentState) -> dict:
    """Rewrite query untuk search ulang."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Rewrite the query to better match document terminology. Return ONLY the new query."),
        ("user", "Original: {original}\nCurrent: {current}\n\nRewritten query:"),
    ])

    chain = prompt | _get_llm(temperature=0.3) | StrOutputParser()
    new_query = chain.invoke({
        "original": state["original_question"],
        "current": state["question"],
    }).strip().strip('"').strip("'")

    logger.info(f"[Agent] Rewritten to: '{new_query[:80]}'")

    return {
        "question": new_query,
        "iterations": state["iterations"] + 1,
        "steps": [AgentStep(
            step="rewrite",
            output=f"Rewrote to: '{new_query[:80]}'"
        )],
    }



def generate_node(state: AgentState) -> dict:
    settings = get_settings()

    if not state["is_relevant"]:
        return {
            "answer": "I couldn't find relevant information in the indexed documents.",
            "steps": [AgentStep(step="generate", output="No relevant docs — returned default message")],
        }

    documents = state["documents"]
    context = "\n\n---\n\n".join(
        f"[Source {i+1}] ({doc.metadata.get('title', 'Doc')})\n{doc.page_content}"
        for i, doc in enumerate(documents)
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer based ONLY on the context. Cite sources. If unsure, say so."),
        ("user", "Context:\n{context}\n\n---\n\nQuestion: {question}"),
    ])

    chain = prompt | ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.chat_model,
        temperature=0.3,
    ) | StrOutputParser()

    answer = chain.invoke({
        "context": context,
        "question": state["original_question"],
    })

    return {
        "answer": answer,
        "steps": [AgentStep(step="generate", output=f"Generated ({len(answer)} chars)")],
    }


def route_after_grade(state: AgentState) -> str:
    if state["is_relevant"]:
        return "generate"
    if state["iterations"] < state["max_iterations"]:
        return "rewrite"
    return "generate"


@lru_cache
def build_agent():
    """Build & compile agent — singleton."""
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade", grade_node)
    workflow.add_node("rewrite", rewrite_node)
    workflow.add_node("generate", generate_node)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade")
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("generate", END)

    workflow.add_conditional_edges(
        "grade",
        route_after_grade,
        {"rewrite": "rewrite", "generate": "generate"},
    )

    return workflow.compile()    


class AgentService:
    """Service wrapper untuk LangGraph agent."""

    def __init__(self):
        self._settings = get_settings()
        self._agent = build_agent()

    def run(self, question: str, max_iterations: int = 3) -> AgentQueryResponse:
        """Run agent dan return structured response."""
        logger.info(f"[Agent] Starting: '{question[:80]}'")

        initial: AgentState = {
            "question": question,
            "original_question": question,
            "documents": [],
            "is_relevant": False,
            "answer": "",
            "iterations": 0,
            "max_iterations": max_iterations,
            "steps": [],
        }

        final = self._agent.invoke(initial)

        sources = [
            SourceChunk(
                doc_id=doc.metadata.get("doc_id", "unknown"),
                title=doc.metadata.get("title", "Untitled"),
                chunk_index=doc.metadata.get("chunk_index", -1),
                text=doc.page_content,
                similarity_score=0.0,
            )
            for doc in final.get("documents", [])
        ]

        return AgentQueryResponse(
            question=question,
            answer=final["answer"],
            iterations=final["iterations"],
            steps=final["steps"],
            sources=sources,
            model=self._settings.chat_model,
        )