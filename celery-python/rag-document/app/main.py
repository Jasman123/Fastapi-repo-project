# app/main.py
"""
FastAPI application — HTTP entry point.

Endpoints:
- POST /documents/ingest    → submit doc untuk ingestion (async)
- GET  /tasks/{task_id}     → cek status task
- POST /chat/query          → query RAG (sync)
- GET  /health              → health check
"""
import structlog
import logging
from fastapi import FastAPI, HTTPException, status
from celery.result import AsyncResult

from app.config import get_settings
from app.models import (
    IngestRequest,
    IngestResponse,
    TaskStatusResponse,
    QueryRequest,
    QueryResponse,
)
from app.tasks import ingest_document
from app.celery_app import celery_app
from app.rag import query_rag

# === Logging setup ===
logging.basicConfig(level=get_settings().log_level)
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),  # Dev: pretty print. Prod: JSONRenderer
    ],
)
logger = structlog.get_logger()

# === FastAPI app ===
app = FastAPI(
    title="Mini RAG API",
    description="RAG system with Celery, ChromaDB, FastAPI, OpenAI",
    version="0.1.0",
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


# === Ingestion Endpoints ===

@app.post(
    "/documents/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,  # 202 = accepted untuk async processing
)
async def ingest(payload: IngestRequest):
    """
    Submit document untuk ingestion.
    
    Kenapa 202 bukan 200:
    - 200 = "request completed"
    - 202 = "request accepted, processing async"
    Lebih semantically correct.
    """
    logger.info("api.ingest.received", doc_id=payload.doc_id, title=payload.title)
    
    try:
        # Submit ke Celery — non-blocking
        # .delay() shortcut untuk .apply_async(args=...)
        task = ingest_document.delay(
            doc_id=payload.doc_id,
            title=payload.title,
            content=payload.content,
        )
        
        return IngestResponse(
            task_id=task.id,
            doc_id=payload.doc_id,
            status="queued",
        )
    
    except Exception as exc:
        # Broker down, dll
        logger.error("api.ingest.submit_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task queue unavailable",
        ) from exc


@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Polling endpoint untuk cek status task.
    
    Status states:
    - PENDING: belum diambil worker (atau task_id tidak valid)
    - STARTED: sedang diproses
    - SUCCESS: selesai sukses, result tersedia
    - FAILURE: gagal, error info tersedia
    - RETRY: sedang di-retry
    """
    result = AsyncResult(task_id, app=celery_app)
    
    response = TaskStatusResponse(
        task_id=task_id,
        status=result.status,
    )
    
    # result.ready() = True kalau SUCCESS atau FAILURE
    if result.ready():
        if result.successful():
            response.result = result.get()  # Safe karena sudah ready
        else:
            # result.info berisi exception
            response.error = str(result.info)
    
    return response


# === Query Endpoint ===

@app.post("/chat/query", response_model=QueryResponse)
async def query(payload: QueryRequest):
    """
    RAG query: retrieve + generate.
    
    Sync (bukan async task) karena:
    - User expect immediate response
    - Latency < 3 detik (acceptable untuk sync HTTP)
    """
    logger.info("api.query.received", question=payload.question[:100])
    
    try:
        result = query_rag(question=payload.question, top_k=payload.top_k)
        return result
    
    except Exception as exc:
        logger.exception("api.query.failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(exc)}",
        ) from exc