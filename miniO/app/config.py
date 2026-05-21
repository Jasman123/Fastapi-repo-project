from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket: str = "documents"

    postgres_dsn: str = "postgresql+asyncpg://postgres:123456@localhost:5432/mydatabase"

    presign_expiry_minutes: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()