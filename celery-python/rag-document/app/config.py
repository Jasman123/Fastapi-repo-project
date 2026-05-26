from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str
    embedding_model: str ="text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"

    redis_url: str = 'redis://localhost:6379/0'

    chroma_persits_dir: str = "./chroma_data"
    chroma_collection_name: str = "documents"

    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 3


    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()