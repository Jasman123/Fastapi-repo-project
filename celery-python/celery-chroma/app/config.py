from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    openai_api_key: str
    model_embedding: str ="text-embedding-3-small",
    redis_url: str = "redis://localhost:6379/0"
    chroma_dir: str = "/chroma_data"
    chroma_collection: str = "documents"

    class Config:
        env_file = ".env"
    
@lru_cache
def get_settings() -> Settings:
    return Settings()

