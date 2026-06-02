from fastapi import APIRouter
from celery.result import AsyncResult
from app.core.celery import celery_app
from app.models.schemas import TaskStatusResponse


router = APIRouter()


@router.get("/{task_id}", response_model = TaskStatusResponse)
async def get_task_status(task_id: str):
    result = AsyncResult(task_id, app = celery_app)
    response = TaskStatusResponse(
        task_id = task_id,
        status = result.status,
    )

    if result.ready():
        if result.successful():
            response.result = result.get()
        else:
            response.error = str(result.info)
    
    return response
