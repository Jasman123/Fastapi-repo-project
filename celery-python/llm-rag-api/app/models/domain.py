from typing import TypedDict, Annotated
from operator import add


class ParseDocument(TypedDict):
    content: str
    metadata: dict


class ChunkedDocument(TypedDict):
    doc_id: str
    title: str
    chunks: list[str]
    chunks_count: int

class IngestionResult(TypedDict):
    doc_id: str
    title: str
    status: str
    chunks_stored: int
    error: str | None


class AgentState(TypedDict):
    question: str
    original_question: str
    documents: list
    is_relevant: bool
    answer: str
    iterations: int
    max_iterations: int
    steps: Annotated[list, add]