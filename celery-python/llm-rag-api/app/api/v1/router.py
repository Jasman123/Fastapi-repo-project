from fastapi import APIRouter
from app.api.v1 import chat, documents, rag, agent, task

api_router = APIRouter()


api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(rag.router, prefix="/rag", tags=["RAG"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"])
api_router.include_router(task.router, prefix="/tasks", tags=["Tasks"])