import os
import logging
from typing import Dict, Callable, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from scheduler.actions import do_morning, do_midday, do_night

class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file="../.env" if os.getenv("ENV", "development") == "development" else None,
    env_file_encoding="utf-8",
    extra="allow",
  )

  # App
  TITLE: str = "LeadditsScheduler"
  VERSION: str = "1.0.0"

  # Logging
  LOG_PATH: str = "./logs/app.log"
  LOGGING_BASE: int = logging.INFO
  TELEGRAM_BASE: int = logging.ERROR

  # API
  API_ENDPOINT: str = "http://localhost:8000"

  # Scheduler (UTC)
  LIST_RULES: bool = False
  TIME_RULES: List[dict] = [
    {"start": "06:00", "end": "10:00", "days": {"mon","tue","wed","thu","fri"}, "action": "morning"},
    {"start": "12:00", "end": "14:00", "action": "midday"},
    {"start": "22:00", "end": "02:00", "action": "night"},
  ]

  # Central action registry
  ACTION_REGISTRY: Dict[str, Callable[[], None]] = {
    "morning": do_morning,
    "midday": do_midday,
    "night":  do_night,
  }

settings = Settings()