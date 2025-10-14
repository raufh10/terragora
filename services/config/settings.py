import os
import logging
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file="../.env" if os.getenv("ENV", "development") == "development" else None,
    env_file_encoding="utf-8",
    extra="allow"
  )

  DEBUG: bool = True
  CODE_ENVIRONMENT: str = "python"

  # API Settings
  TITLE: str = "LeadditsAPI"
  VERSION: str = "1.0.0"
  DESC: str = "Development-ready FastAPI application"
  CORS_ORIGIN: list[str] = [
    "*"
  ]

  # Logging Settings
  API_LOG_PATH: str = "./logs/api.log"
  LOGGING_BASE: int = logging.INFO
  TELEGRAM_BASE: int = logging.ERROR

  # Extraction Settings
  REDDIT_USERNAME: str = "Icy_Pie_3434"
  USER_AGENT: str = f"{CODE_ENVIRONMENT}:{TITLE}:{VERSION} (by u/{REDDIT_USERNAME})"
  IS_READ_ONLY: bool = True
  TIMEOUT: int = 60

settings = Settings()
