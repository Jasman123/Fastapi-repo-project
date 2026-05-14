from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, HTTPException, File
from pydantic import BaseModel

from .ingestion import ingest_file, get_vectorstore
from .retrieval import query_documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    vectorstore = get_vectorstore()
    yield
    vectorstore.persist()


app = FastAPI(lifespan=lifespan, 
            title="RAG Document Q&A API",
            description="An API for ingesting documents and querying them using Retrieval-Augmented Generation (RAG)")


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str
    source: list[str]
    chunks_used: int

@app.post("/ingest", status_code=201)
async def ingest(file: UploadFile = File(...)):
    return await ingest_file(file)

@app.post("/ask", response_model=AnswerResponse)
async def ask(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(
            status_code = 400,
            detail = "Question cannot be empty."
        )
    return await query_documents(request.question, get_vectorstore())

@app.get("/status")
def status():
    vs = get_vectorstore()
    count = vs._collection.count()
    return {"chunks_stored": count, "status": "ready" if count > 0 else "empty"}

@app.delete("/clear", status_code=204)
def clear_vectorstore():
    vs = get_vectorstore()
    vs._collection.delete(where={"source": {"$ne": ""}})