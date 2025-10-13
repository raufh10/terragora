import os
from pydantic import SecretStr
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict

class Credentials(BaseSettings):
  model_config = SettingsConfigDict(
    env_file="../.env" if os.getenv("ENV", "development") == "development" else None,
    env_file_encoding="utf-8",
    extra="allow"
  )

  # General Creds
  supabase_url: SecretStr | None = None
  supabase_key: SecretStr | None = None
  telegram_user_id: SecretStr | None = None
  telegram_bot_token: SecretStr | None = None

  # Extraction Creds
  openai_api_key: SecretStr | None = None

  @property
  def OPENAI_API_KEY(self) -> str:
    if not self.openai_api_key:
      raise ValueError("OPENAI_API_KEY not set.")
    return quote_plus(self.openai_api_key.get_secret_value())

credentials = Credentials()
