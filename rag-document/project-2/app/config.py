from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPEN_API_KEY: str
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    COLLECTION_NAME: str = "documents"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 3

    model_config = {"env_file": ".env"}

settings = Settings()
