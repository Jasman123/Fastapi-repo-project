from pydantic_settings import BaseSettings
from pathlib import Path

ENV_PATH = Path(__file__).parent.parent / ".env"

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    COLLECTION_NAME: str = "documents"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 3

    model_config = {"env_file": str(ENV_PATH)}

settings = Settings()
