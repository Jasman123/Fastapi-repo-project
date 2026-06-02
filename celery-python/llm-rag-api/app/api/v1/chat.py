from fastapi import APIRouter, HTTPException, status
from app.models.schemas import (
    ChatRequest,
    BatchChatRequest,
    SummarizeRequest,
    TaskSubmittedResponse,
    BatchTaskResponse,
)
from app.tasks.chat_tasks import ask_llm_task, summarize_task, process_batch_task
router = APIRouter()

@router.post("/ask", response_model = TaskSubmittedResponse, status_code = 202)
async def ask(payload: ChatRequest):
    
    try :
        orchestrator = process_batch_task.delay(
            questions = payload.questions,
            system_prompt = payload.system_prompt,
            temperature = payload.temperature,
        )
        batch_info = orchestrator.get(timeout =10)
        return BatchTaskResponse(
            task_ids=[t["task_id"] for t in batch_info["task"]],
            total = batch_info["total_submitted"],
            status = "queued",
        )
    except Exception as exc:
        raise HTTPException(status_code = 503, detail = "task queue unavailabe")

@router.post("/batch", response_model = BatchTaskResponse, status_code = 202)
async def  batch(payload: BatchChatRequest):
    try:
        orchestrator = process_batch_task.delay(
            questions = payload.questions,
            system_prompt = payload.system_prompt,
            temperature = payload.temperature,
        )
        batch_info = orchestrator.get(timeout = 10)
        return BatchTaskResponse(
            task_ids=[t["task_id"] for t in batch_info["task"]],
            total = batch_info["total_submitted"],
            status = "queued",
        )
    except Exception as exc:
        raise HTTPException(status_code = 503, detail = str(exc))

@router.post("/summarize", response_model = TaskSubmittedResponse, status_code = 202)
async def summarize(payload: SummarizeRequest):
    try:
        task = summarize_task.delay(
            text = payload.text,
            max_sentences = payload.max_sentences,
        )
        return TaskSubmittedResponse(task_id = task.id, status="queued")
    except Exception:
        raise HTTPException(status_code=503, detail="task queue unavailable")