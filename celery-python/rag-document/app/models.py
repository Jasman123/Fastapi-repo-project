from pydantic import BaseModel, Field
from typing import Literal, Optional



class IngestRequest(BaseModel):
    doc_id: str = Field(..., min_length=1, max_length=100, description="Unique document identifier")
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=10, description="Raw text content")

class IngestResponse(BaseModel):
    task_id: str
    doc_id: str
    status: Literal["queued"]
    message: str = "Document ingestion started. Poll/task/{task_id} for status"

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10, description = "Number of chunks to retrieve")


class SourceChunk(BaseModel):
    doc_id: str
    chunk_index: int
    text: str
    similarity_score: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceChunk]
    model: str




