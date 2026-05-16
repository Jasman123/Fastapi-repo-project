from pydantic_settings import BaseSettings
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    model_config = {"env_file": str(ENV_PATH)}

settings = Settings()
