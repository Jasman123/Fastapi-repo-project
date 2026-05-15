from contextlib import asynccontextmanager
from pydantic import BaseModel
from pathlib import Path
from fastapi import FastAPI
from .config import settings
from .ingestion import ensure_collection
from .routers import chat

@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_collection()
    Path("uploads").mkdir(exist_ok=True)
    yield

app = FastAPI(title="RAG — Milvus + LangGraph", lifespan=lifespan)

app.include_router(chat.router)

@app.get("/health")
def health():
    return {
        "status":    "ok",
        "vector_db": "Milvus",
        "framework": "LangGraph",
        "nodes":     8,
        "edges":     4,
        "sessions":  len(chat.session_store),
    }