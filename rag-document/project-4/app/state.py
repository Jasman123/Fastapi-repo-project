from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.documents import Document
from langgraph.graph.message import add_messages


class GraphState(TypedDict):

    question: str
    original_question: str
    query_type: str


    documents: list[Document]
    doc_grade: str
    rewrite_count: str

    generation: str
    answer_grade: str

    chat_history: Annotated[list, add_messages]









