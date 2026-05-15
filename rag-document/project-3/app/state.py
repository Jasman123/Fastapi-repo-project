from typing import TypedDict, Annotated
from langchain_core.documents import Document
from langgraph.graph.message import add_messages
import operator

class GraphState(TypedDict):
    question: str
    documents: list[Document]
    generation: str
    chat_history: Annotated[list, add_messages]
    web_search: bool
    doc_grade: str



