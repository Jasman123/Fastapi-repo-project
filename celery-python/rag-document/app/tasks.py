import structlog
from celery.exceptions import SoftTimeLimitExceeded
from openai import APIError, RateLimitError as OpenAIRateLimitError


from app.celery_app import celery_app
from app.config import get_settings
from app.openai_client import generate_embeddings_batch
from app.chroma_client import get_collection

logger = structlog.get_logger()

def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0


    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks

@celery_app.task(
    bind=True,
    name="app.tasks.ingest_document",
    autoretry_for=(ConnectionError, TimeoutError, OpenAIRateLimitError),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
)

def ingest_document(self, doc_id: str, title: str, content: str) -> dict:
    settings = get_settings()
    log = logger.bind(
        task_id = self.request.id,
        doc_id = doc_id,
        retry_count = self.request.retries,
    )
    log.info("ingest.started", title = title, content_length = len(content))

    try:

        chunks = _chunk_text(
            content,
            chunk_size=settings.chunk_size,
            overlap= settings.chunk_overlap,
        )
        log.info("ingest.chunked", chunk_count= len(chunks))
        log.info("ingest.embedding", chubnks=len(chunks))
        embeddings = generate_embeddings_batch(chunks)
        log.info("ingest.embedded", embedding_dim = len(embeddings[0]))

        collection = get_collection()

        ids = [f"{doc_id}:: chunk_{i}" for i in range(len(chunks))]
        metadatas =[
            {
                "doc_id" : doc_id,
                "tittle" : title,
                "chunk_index" : i,
                "chunk_count" : len(chunks),
            }
            for i in range(len(chunks))
        ]

        collection.upsert(
            ids = ids, embeddings = embeddings, documents = chunks, metadatas = metadatas,
        )

        result = {
            "doc_id": doc_id,
            "status": "sucess",
            "chunks_stored": len(chunks),
            "embedding_model": settings.embedding_model,
        }
        log.info("ingest.completed", **result)
        return result
    
    except SoftTimeLimitExceeded:
        log.warning("ingest.soft_timeout")
        raise

    except APIError as exc:
        log.error("ingest.openai_erro", error = str(exc), status=getattr(exc, "status_code", None))
        raise
    except Exception as exc:
        log.exception("inges.unexpected_error")
        raise
    