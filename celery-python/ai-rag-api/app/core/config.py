from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    openai_api_key: str

    redis_url: str = "redis://localhost:6379/0"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ai_rag"
    postgres_user: str = "postgres"
    postgres_password: str ="postgres"


    chroma_dir: str ="./chorma_data"
    chroma_collection: str = "documents"

    upload_dir: str = "./uploads"

    class Config:
        env_file = ".env"

    @property
    def postgres_url(self) -> str:

        return (
           f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}" 
        )
    
    @lru_cache
    def get_settings() -> Settings:
        return Settings()