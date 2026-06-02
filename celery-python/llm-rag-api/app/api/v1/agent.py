from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_agent_service
from app.models.schemas import AgentQueryRequest, AgentQueryResponse
from app.services.agent_service import AgentService


router = APIRouter()

@router.post("/query", response_model = AgentQueryResponse)
async def agent_query(payload: AgentQueryRequest, service: AgentService = Depends(get_agent_service),):
    try:
        return service.run(
            question = payload.question,
            max_iterations = payload.max_iterations,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    