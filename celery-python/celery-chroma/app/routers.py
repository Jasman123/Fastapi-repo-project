from fastapi import APIRouter, HTTPException, status
from celery.result import AsyncResult
from pydantic import BaseModel, Field


from app.celery_app import celery_app
from app.tasks import ingest_task
from app.services import answer_question

router = APIRouter()


class IngestRequest(BaseModel):
    doc_id: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=10)

class IngestResponse(BaseModel):
    task_id: str
    status: str = "queued"
    message: str = "Task submitted. Poll /tasks/{task_id} for status."


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str       # PENDING / STARTED / SUCCESS / FAILURE
    result: dict | None = None
    error: str | None = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3)
    top_k: int = Field(default=3, ge=1, le=10)


@router.post("/ingest", response_model=IngestResponse, status_code= status.HTTP_202_ACCEPTED)
async def ingest(payload: IngestRequest):
    try:
        task = ingest_task.delay(doc_id= payload.doc_id, title=payload.title, content=payload.content,)
    
    except Exception:
        raise HTTPException(
            status_code=503, detail="Task queue tidak tersedia, Pastika Redis berjalan."
        )
    return IngestResponse(task_id=task.id)

@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    response = TaskStatusResponse(task_id=task_id, status=result.status)

    if result.ready():
        if result.successful():
            response.result = result.get()
        else:
            response.error = str(result.info)

    
    return response


@router.post("/ask")
async def ask(payload: AskRequest):
    result = answer_question(question=payload.question, top_k=payload.top_k,)
    return result




