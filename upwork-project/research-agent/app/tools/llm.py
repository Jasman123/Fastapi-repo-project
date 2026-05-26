import logging
from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from app.utils.config import settings
from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:

    if settings.LLM_PROVIDER == "openai":
        

        logger.info(f"LLM : OpenAI {settings.OPENAI_API_KEY}")
        return ChatOpenAI( model = settings.OPENAI_MODEL, api_key = settings.OPENAI_API_KEY, temperature = 0.3, max_tokens = 2040, timeout = 60,)
    
    elif settings.LLM_PROVIDER =="vertex":
        logger.info(f"LLM: Vertex AI {settings.VERTEX_GEN_MODEL}")
        return ChatVertexAI( model_name = settings.VERTEX_GEN_MODEL, project = settings.GCP_PROJECT, location = settings.GCP_REGION, temperature = 0.3, max_output_token = 2048,)

    else :
        raise ValueError(f"Unknown LLM_PROVIDER : {settings.LLM_PROVIDER}! use 'openai' or 'vertex")
    
    


