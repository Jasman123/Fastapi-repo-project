from celery import Celery
from app.core.config import get_settings


settings = get_settings()

celery_app = Celery(
    "ai_rag",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.document_tasks"],
)


celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    task_track_started=True,
    result_expires=86400,
    task_time_limit=600,
    task_soft_time_limit=540,
    worker_prefect_multiplier=1,
)
