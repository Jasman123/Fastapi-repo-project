from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    MILVUS_URI: str = "http://localhost:19530"
    MILVUS_COLLECTION: str = "documents"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    RETRIEVER_K: int = 4
    MAX_REWRITE_ATTEMPTS: str = 3

    model_config = {"env_file": ".env"}

settings = Settings()