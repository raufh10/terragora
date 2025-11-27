import os
import logging
import yaml
from typing import Optional, Dict, Callable, List

from pydantic import SecretStr, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from scheduler import actions


def load_yaml_config(file_path: str) -> dict:
  if not os.path.exists(file_path):
    raise FileNotFoundError(f"❌ Config YAML not found: {file_path}")

  try:
    with open(file_path, "r", encoding="utf-8") as f:
      return yaml.safe_load(f) or {}
  except Exception as e:
    raise RuntimeError(f"❌ Failed to read YAML config: {e}")


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

  # Loaded dynamically from YAML
  TIME_RULES: List[dict] = []
  ACTION_REGISTRY: Dict[str, Callable[..., None]] = {}

  @staticmethod
  def _resolve_actions(action_map: dict) -> Dict[str, Callable[..., None]]:
    resolved = {}

    for action_name, func_name in action_map.items():
      if not hasattr(actions, func_name):
        raise ValueError(f"❌ Unknown action '{func_name}' mapped for '{action_name}' in YAML")
      resolved[action_name] = getattr(actions, func_name)

    return resolved

  @model_validator(mode="after")
  def load_external_config(self) -> "Settings":
    yaml_path = "data/config.yaml"

    config = load_yaml_config(yaml_path)

    # ---- TIME RULES ----
    if "time_rules" not in config:
      raise ValidationError(f"❌ Missing required key `time_rules` in {yaml_path}")

    self.TIME_RULES = config["time_rules"]

    # ---- ACTION REGISTRY ----
    if "actions" not in config:
      raise ValidationError(f"❌ Missing required key `actions` in {yaml_path}")

    self.ACTION_REGISTRY = self._resolve_actions(config["actions"])

    # ---- Environment override ----
    env_type_val = (self.env_type.get_secret_value() if self.env_type else "").strip()
    if env_type_val == "local_machine":
      self.API_ENDPOINT = "http://127.0.0.1:8000"

    return self


settings = Settings()
