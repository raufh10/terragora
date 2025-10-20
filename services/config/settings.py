import os
import logging
from typing import Dict, Callable, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from scheduler.actions import (
  do_extraction,
  do_transform,
  do_load
)

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
  API_ENDPOINT: str = "http://127.0.0.1:8000"

  # Scheduler (UTC)
  LIST_RULES: bool = False
  TIME_RULES: List[dict] = [
    {"start": "00:00", "end": "23:59", "action": "test"},
    {"start": "10:00", "end": "11:00", "action": "collect"},
    {"start": "11:00", "end": "12:00", "action": "label"},
    {"start": "12:00", "end": "13:00", "action": "send"}
  ]

  # Central action registry
  ACTION_REGISTRY: Dict[str, Callable[[], None]] = {
    "test": do_transform,
    "collect":  do_extraction,
    "label": do_transform,
    "send": do_load
  }

settings = Settings()
