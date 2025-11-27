import os
import logging
from typing import Optional, Dict, Callable, List

from pydantic import SecretStr, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from scheduler import actions

class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=".env" if os.getenv("ENV", "development") == "development" else None,
    env_file_encoding="utf-8",
    extra="allow",
  )

  env_type: Optional[SecretStr] = Field(default=None, alias="ENV_TYPE")

  TITLE: str = "LeadditsScheduler"
  VERSION: str = "1.0.0"

  LOG_PATH: str = "./logs/app.log"
  LOGGING_BASE: int = logging.DEBUG
  TELEGRAM_BASE: int = logging.ERROR

  API_ENDPOINT: str = "http://leaddits_api.railway.internal:8080"

  LIST_RULES: bool = False
  TIME_RULES: List[dict] = [
    {"start": "00:00", "end": "23:59", "action": "all"},
  ]

  ACTION_REGISTRY: Dict[str, Callable[..., None]] = {
    "all": actions.all,
  }

  @model_validator(mode="after")
  def _compute_api_endpoint(self) -> "Settings":
    env_type_val = (self.env_type.get_secret_value() if self.env_type else "").strip()
    if env_type_val == "local_machine":
      self.API_ENDPOINT = "http://127.0.0.1:8000"
    return self

settings = Settings()
