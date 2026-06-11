from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ResearchAgent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    API_KEY: str = Field(default="dev-key-change-me")


    LLM_PROVIDER: str = Field(default="openai")
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_MODEL: str = Field(default="gpt-4o")

    GCP_PROJECT: str = Field(default="")
    GCP_REGION: str = Field(default="us-central1")
    VERTEX_GEN_MODEL: str = Field(default="gemini-1.6-flash-002")

    TAVILY_API_KEY: str = Field(default="")
    MAX_SEARCH_RESULTS: int = Field(default=5)

    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./research.db")

    SEARCH_QUERIES_COUNT: int = Field(default=4)
    LLM_TEMPERATURE: float = Field(default=0.3)
    LLM_MAX_TOKENS: int = Field(default=2048)


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()



