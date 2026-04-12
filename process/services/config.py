import os
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Configs(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=".env" if os.getenv("ENV", "development") == "development" else None,
    env_file_encoding="utf-8",
    extra="allow"
  )

  # Telegram creds
  telegram_bot_token: SecretStr | None = None
  telegram_user_id: SecretStr | None = None

  # pgvector creds
  conn_str: SecretStr | None = None
  prod_conn_str: SecretStr | None = None

  # OpenAI creds
  openai_api_key: SecretStr | None = None

  # General settings
  env: SecretStr | None = None

  @computed_field
  @property
  def active_conn_str(self) -> SecretStr | None:
    if self.env.get_secret_value().lower() == "production":
      return self.prod_conn_str
    return self.conn_str

configs = Configs()
