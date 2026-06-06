import logging
from celery import Task
from openai import RateLimitError

from app.celery_app import celery_app
from app.services import ingest_document

logger = logging.getLogger(__name__)

class BaseTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task sukses: {task_id}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task gagal: {task_id} — {exc}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(f"Task retry: {task_id} — {exc}")

@celery_app.task(
    bind=True,  base=BaseTask, name="ai_tasks.ingest", autoretry_for=(ConnectionError, TimeoutError, RateLimitError), max_retries=3, retry_backoff=True, retry_backoff_max=60, retry_jitter=True,
)
def ingest_task(self, doc_id: str, title: str, content: str) -> dict:
    task_id = self.request.id
    attempt = self.request.retries +1

    logger.info(
        f"[{task_id}] ingest_task mulai "
        f"(percobaan ke-{attempt}): doc_id={doc_id}"
    )

    result = ingest_document(doc_id=doc_id, title=title, content=content)
    logger.info(
        f"[{task_id}] ingest_task selesai: "
        f"{result['chunks_stored']} chunks"
    )

    return result