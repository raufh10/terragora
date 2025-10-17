import os
import logging
from typing import Dict, Callable, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from scheduler import actions

class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=".env" if os.getenv("ENV", "development") == "development" else None,
    env_file_encoding="utf-8",
    extra="allow",
  )

  # App
  TITLE: str = "LeadditsScheduler"
  VERSION: str = "1.0.0"

  # Logging
  LOG_PATH: str = "./logs/app.log"
  LOGGING_BASE: int = logging.DEBUG
  TELEGRAM_BASE: int = logging.ERROR

  # API
  #API_ENDPOINT: str = "https://leaddits-api-production.up.railway.app/"
  API_ENDPOINT: str = "https://leaddits-api.railway.internal:8080/"

  # Scheduler (UTC)
  LIST_RULES: bool = False
  TIME_RULES: List[dict] = [
    {"start": "00:00", "end": "01:00", "action": "collect"},
    {"start": "02:00", "end": "03:00", "action": "label"},
    {"start": "03:00", "end": "04:00", "action": "send"}
  ]

  # Central action registry
  ACTION_REGISTRY: Dict[str, Callable[[], None]] = {
    "collect":  actions.do_extraction,
    "label": actions.do_transform,
    "send": actions.do_load
  }

settings = Settings()
