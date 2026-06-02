from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str ="LLM RAG API"
    app_env: str = "development"
    debug: bool = True

    openai_api_key: str
    chat_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    redis_url: str = 'redis://localhost:6379/0'

    chroma_persits_dir: str = "./chroma_data"
    chroma_collection_name: str = "documents"

    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 3


    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50


    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024
    

@lru_cache
def get_settings() -> Settings:
    return Settings()