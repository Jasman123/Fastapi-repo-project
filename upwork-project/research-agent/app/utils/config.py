

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ── API security ──────────────────────────────────────────────────────────
    API_KEY: str = Field(default="dev-key-change-me")

    # ── LLM provider ─────────────────────────────────────────────────────────
    LLM_PROVIDER: str = Field(default="openai")  # "openai" | "vertex"

    # ── OpenAI ────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_MODEL: str = Field(default="gpt-4o")

    # ── GCP / Vertex AI ───────────────────────────────────────────────────────
    GCP_PROJECT: str = Field(default="my-gcp-project")
    GCP_REGION: str = Field(default="us-central1")
    VERTEX_GEN_MODEL: str = Field(default="gemini-1.5-flash-002")

    # ── Search ────────────────────────────────────────────────────────────────
    TAVILY_API_KEY: str = Field(default="")  # If empty, falls back to DuckDuckGo

    # ── Report ────────────────────────────────────────────────────────────────
    REPORT_OUTPUT_DIR: str = Field(default="/tmp/reports")
    MAX_SEARCH_RESULTS_PER_QUERY: int = Field(default=5)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Module-level singleton for convenience
settings = get_settings()