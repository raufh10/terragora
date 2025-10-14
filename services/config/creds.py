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
  client_id: SecretStr | None = None
  @property
  def CLIENT_ID(self) -> str:
    if not self.client_id:
      raise ValueError("CLIENT_ID not set.")
    return quote_plus(self.client_id.get_secret_value())

  cliend_secret: SecretStr | None = None
  @property
  def CLIENT_SECRET(self) -> str:
    if not self.cliend_secret:
      raise ValueError("CLIENT_SECRET not set.")
    return quote_plus(self.cliend_secret.get_secret_value())

  # Transform Creds
  openai_api_key: SecretStr | None = None

  @property
  def OPENAI_API_KEY(self) -> str:
    if not self.openai_api_key:
      raise ValueError("OPENAI_API_KEY not set.")
    return quote_plus(self.openai_api_key.get_secret_value())

credentials = Credentials()
