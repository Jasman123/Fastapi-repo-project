from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_rag_service
from app.models.schemas import RAGQueryRequest, RAGQueryResponse
from app.services.rag_service import RAGService

router = APIRouter()

@router.post("/query", response_model = RAGQueryResponse)
async def query( payload: RAGQueryRequest, service: RAGService = Depends(get_rag_service),):
    try:
        return service.query(
            question = payload.question,
            top_k = payload.top_k,
        )
    except Exception as exc:
        raise HTTPException(status_code = 500, detail = str(exc))
