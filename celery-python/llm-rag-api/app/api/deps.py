from functools import lru_cache
from app.services.document_service import DocumentService
from app.services.rag_service import RAGService
from app.services.agent_service import AgentService


def get_document_service() -> DocumentService:
    return DocumentService()

def get_rag_service() -> RAGService:
    return RAGService()

def get_agent_service() -> AgentService:
    return AgentService()


