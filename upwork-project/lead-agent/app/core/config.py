from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    OPENAI_API_KEY: str
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"

    PLAYWRIGHT_TIMEOUT_MS: int = 15000
    PLAYWRIGHT_HEADLESS: bool = True

    SCORE_KEYWORDS: str = "python,api,automation,saas,fastapi,langchain,ai,machine learning"
    SCORE_THRESHOLD_HOT: int = 70
    SCORE_THRESHOLD_WARM: int = 40

    GOOGLE_SHEETS_CREDENTIALS_PATH: str = "./storage/google_credentials.json"
    GOOGLE_SHEET_ID: str = ""

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMPT_USER: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_RECIPIENT: str = ""


    SQLITE_PATH: str = ".storage/leads.db"

    APP_NAME: str = "Lead Qualification Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

@lru_cache
def get_settings() -> Settings:
    return Settings