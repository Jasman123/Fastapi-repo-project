from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery("ai_task", broker=settings.redis_url, backend=settings.redis_url,)

celery_app.conf.update(
    task_serializer="json",
    result_serialize="json",
    accept_content=["json"],

    task_acks_late=True,

    task_track_started=True,

    result_expires=3600,
)