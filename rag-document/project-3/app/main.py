from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .config import settings
from .ingestion import ensure_collection
from .routers import chat

@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_collection()
    Path("uploads").mkdir(exist_ok=True)

    yield


app = FastAPI(
    title = 'RAG with LangGraph and Qdrant', lifespan=lifespan
)


app.include_router(chat.router)

@app.get("/health")
def health():
    return {
        "status":     "ok",
        "vector_db":  "Qdrant",
        "framework":  "LangGraph",
        "sessions":   len(chat.session_store),
    }
