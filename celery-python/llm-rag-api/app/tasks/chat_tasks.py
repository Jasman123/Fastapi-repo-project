import logging
from celery.exceptions import SoftTimeLimitExceeded
from openai import RateLimitError as OpenAIRateLimitError

from app.core.celery import celery_app
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)


@celery_app.task(
    bind = True,
    name = "app.tasks.chat_task.ask_llm",
    autoretry_for = (ConnectionError, TimeoutError, OpenAIRateLimitError),
    max_retries = 3,
    retry_backoff = True,
    retry_jitter = True,
)
def ask_llm_task(self, question: str, system_prompt: str|None = None, temperature: float = 0.7) -> dict:
    logger.info(f"[Task {self.request.id}] ask_llm: '{question[:80]}'")

    try:
        service = ChatService()
        result = service.ask(
            question = question,
            system_prompt = system_prompt,
            temperature = temperature,
        )
        result["attempts"] = self.request.retries + 1
        return result
    
    except SoftTimeLimitExceeded:
        raise


@celery_app.task(
    bind = True,
    name = "app.tasks.chat_task.summarize",
    autoretry_for = (ConnectionError, TimeoutError, OpenAIRateLimitError),
    max_retries = 3,
    retry_backoff = True,
)
def summarize_task(self, text: str, max_sentences: int = 3) -> dict:
    logger.info(f"[Task {self.request.id}] summarize: {len(text)} chars")

    try:
        service = ChatService()
        return service.summarize(
            text = text,
            max_sentences = max_sentences,
        )
    except SoftTimeLimitExceeded:
        raise


@celery_app.task(
    name = "app.tasks.chat_task.process_batch"
)
def process_batch_task(questions : list[str], system_prompt: str|None = None, temperature: float = 0.7) -> dict:
    tasks = []
    for question in questions:
        result = ask_llm_task.delay(
            question = question,
            system_prompt = system_prompt,
            temperature = temperature,
        )
        tasks.append({
            "question" : question[:50] + "..." if len(question) > 50 else question,
            "task_id" : result.id,
        })

    return {"total_submitted" : len(questions), "task" : tasks}
    