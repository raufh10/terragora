import os
from pydantic import SecretStr, computed_field
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
  MAX_RETRIES: int = 2
  RETRY_DELAY: int = 1

  # OpenAI settings
  ProductExtractionPrompt: str = """
    Extract the price and a concise summary (1–3 sentences) of the seller’s notes 
    from the marketplace post.
    Ensure high precision:
    - Do not infer or guess missing details
    - Only use explicitly stated information
  """

  @computed_field
  @property
  def active_conn_str(self) -> SecretStr | None:
    if self.env.get_secret_value().lower() == "production":
      return self.prod_conn_str
    return self.conn_str

configs = Configs()
