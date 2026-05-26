from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "rag_app",
    broker = settings.redis_url,
    backend = settings.redis_url,
    include = ["app.tasks"],
)

celery_app.conf.update(
    task_serializer = "json",
    accept_content=["json"],
    result_serializer="json",

    task_acks_late = True,
    task_reject_on_worker_lost = True
    task_track_started = True,


    Task_time_limit = 600,
    task_soft_time_limit=540,


    worker_prefecth_multiplier =1,
    worker_max_task_per_child=50,

    result_expires = 3600,
    timezone = "Asia/Jakarta",
    enable_utc = True,
)