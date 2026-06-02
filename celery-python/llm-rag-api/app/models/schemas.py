from pydantic import BaseModel, Field
from typing import Literal, Optional



class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    system_prompt: Optional[str] = None
    temperature: float = Field(default= 0.7, ge=0.0, le=1.0)


class BatchChatRequest(BaseModel):
    questions: list[str] = Field(..., min_length=1, max_length=20)
    system_prompt: Optional[str] = None
    temperature: float = Field(default= 0.7, ge=0.0, le=1.0)

class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000)
    max_sentences: int = Field(default=3, ge=1, le=10)



class TextIngestRequest(BaseModel):
    doc_id: str = Field(..., min_length=1, max_length=100, description="Unique document identifier")
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=10, description="Raw text content")

class DocumentInfo(BaseModel):
    doc_id: str
    title: str
    source_type: str
    chunks_count: int


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10, description = "Number of chunks to retrieve")


class SourceChunk(BaseModel):
    doc_id: str
    title: str
    chunk_index: int
    text: str
    similarity_score: float

class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceChunk]
    model: str





class AgentQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    max_iterations: int = Field(default=3, ge=1, le=5, description="Maximum reasoning steps/iterations for the agent")


class AgentStep(BaseModel):
    step: str
    output: str

class AgentQueryResponse(BaseModel):
    question: str
    answer: str
    iterations: int
    steps: list[AgentStep]
    sources: list[SourceChunk]
    model: str



class TaskSubmittedResponse(BaseModel):
    task_id: str
    status: Literal["queued"]
    message: str = "Task has been submitted. Poll api/v1/task/{task_id} for status"

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None

class BatchTaskResponse(BaseModel):
    task_ids: list[str]
    total: int
    status: Literal["queued"]

class PDFUploadResponse(BaseModel):
    task_id: str
    doc_id: str
    filename: str
    file_size_bytes: int
    status: Literal["queued"]

class DeleteResponse(BaseModel):
    doc_id: str
    deleted: bool
    chunks_removed: int

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None    

