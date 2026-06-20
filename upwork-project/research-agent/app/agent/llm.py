import logging
from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache
def get_llm() -> BaseChatModel:

    if settings.LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        logger.info(f"LLM: OpenAI/ {settings.OPENAI_MODEL}")
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=60,
        )
    if settings.LLM_PROVIDER == "vertex":
        from langchain_google_vertexai import ChatVertexAI
        logger.info(f"LLM: Vertex AI / {settings.VERTEX_GEN_MODEL}")
        return ChatVertexAI(
            model_name=settings.VERTEX_GEN_MODEL,
            project=settings.GCP_PROJECT,
            location=settings.GCP_REGION,
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_TOKENS,
        )
    
    if settings.LLM_PROVIDER == "local":
        from langchain_openai import ChatOpenAI
        logger.info(f"LLM: Local / {settings.LOCAL_MODEL} @ {settings.LOCAL_BASE_URL}")
        return ChatOpenAI(
            model=settings.LOCAL_MODEL,
            base_url=settings.LOCAL_BASE_URL,
            api_key=settings.LOCAL_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=120,
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER}."
        "Valid values: 'openai', 'vertex', 'local'."
    )