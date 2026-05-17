"""
Centralised configuration — reads from environment variables.
All secrets stay out of source code.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    anthropic_api_key: str = "sk-demo-key"   # override via .env
    llm_model: str = "claude-3-5-haiku-20241022"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1024

    # Agent behaviour
    max_retries: int = 2
    escalation_confidence_threshold: float = 0.55   # below → human escalation

    # GCP (optional — used when deploying to Cloud Run)
    gcp_project_id: str = "demo-project"
    gcp_region: str = "asia-southeast1"

    # App
    app_env: str = "development"
    log_level: str = "INFO"


settings = Settings()
