import os
import logging
from pydantic import SecretStr
from urllib.parse import quote_plus
from typing import Dict, Callable, List
from pydantic_settings import BaseSettings, SettingsConfigDict

from scheduler.actions import do_all
from scheduler.test_actions import do_test

class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=".env" if os.getenv("ENV", "development") == "development" else None,
    env_file_encoding="utf-8",
    extra="allow",
  )

  # Environments
  env_type: SecretStr | None = None

  # App
  TITLE: str = "LeadditsScheduler"
  VERSION: str = "1.0.0"

  # Logging
  LOG_PATH: str = "./logs/app.log"
  LOGGING_BASE: int = logging.DEBUG
  TELEGRAM_BASE: int = logging.ERROR

  # API
  env_type_var: str = env_type.get_secret_value()

  if env_type_var == "local_machine":
    API_ENDPOINT: str = "http://127.0.0.1:8000"
  else:
    API_ENDPOINT: str = "http://leaddits_api.railway.internal:8080"

  # Scheduler (UTC)
  LIST_RULES: bool = False
  TIME_RULES: List[dict] = [
    {
      "start": "00:00",
      "end": "23:59",
      "action": "test"
    },
  ]

  # Central action registry
  ACTION_REGISTRY: Dict[str, Callable[[], None]] = {
    "all": do_all,
    "test": do_test
  }

settings = Settings()
