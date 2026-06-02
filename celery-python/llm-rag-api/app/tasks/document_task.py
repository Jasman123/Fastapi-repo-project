import logging
from celery.exceptions import SoftTimeLimitExceeded
from openai import RateLimitError as OpenAIRateLimitError, APIError


from app.core.celery import celery_app
from app.services.document_service import DocumentService
from app.utils.pdf_parser import parse_pdf
from app.utils.file_handler import delete_file


logger = logging.getLogger(__name__)

@celery_app.task(
    bind = True,
    name = "app.tasks.cdocumnet_task.ingest_text",
    autoretry_for = (ConnectionError, TimeoutError, OpenAIRateLimitError),
    max_retries = 3,
    retry_backoff = True,
    retry_jitter = True,
)

def ingest_text_task(self, doc_id: str, title: str, content: str) -> dict:
    logger.info(f"[Task {self.request.id}] ingest_text:  doc_id={doc_id}")

    try:
        service = DocumentService()
        return service.ingest_text(doc_id = doc_id, title = title, content = content)
    except SoftTimeLimitExceeded:
        logger.warning(f"[Task {self.request.id}] soft timeout!")
        raise
    except Exception as exc:
        logger.exception(f"[Task {self.request.id}] Error ingesting text: {exc}")
        raise



@celery_app.task(
    bind = True,
    name = "app.tasks.document_task.ingest_pdf",
    autoretry_for = (ConnectionError, TimeoutError, OpenAIRateLimitError),
    max_retries = 3,
    retry_backoff = True,
    retry_backoff_max = 60,
    retry_jitter = True,
    soft_time_limit = 300,
    time_limit = 360,
)
def ingest_pdf_task(self, file_path: str, doc_id: str, title: str | None = None) -> dict:
    logger.info(f"[Task {self.request.id}] ingest_pdf: {file_path}")

    try:
        pdf_data = parse_pdf(file_path)
        final_title = title or pdf_data.get("metadata", {}).get("pdf_title") or pdf_data["metadata"]["filename"]
        service = DocumentService()
        result = service.ingest_from_parsed_pdf(
            doc_id = doc_id,
            title = final_title,
            pdf_data = pdf_data,
        )
        delete_file(file_path)
        return result
    
    except SoftTimeLimitExceeded:
        logger.warning(f"[task {self.request.id}] Soft timeout!")
        raise

    except FileNotFoundError as exc:
        logger.error(f"[Task {self.request.id}] File not found: {exc}")
        raise
    
    except Exception as exc:
        logger.exception(f"[Task {self.request.id}] Failed: {exc}")
        raise
    