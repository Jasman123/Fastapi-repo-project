from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path

ENV_PATH = Path(__file__).parent.parent / ".env"

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str
    QDRANT_COLLECTION: str = "documents"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    RETRIEVER_K: int = 5
    QDRANT_VECTOR_SIZE: int = 1536

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v.startswith("sk-"):
            raise ValueError("OPENAI_API_KEY must start with 'sk-'")
        return v

    model_config = {
        "env_file": str(ENV_PATH),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

settings = Settings()