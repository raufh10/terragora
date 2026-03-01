import os
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Configs(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=".env" if os.getenv("ENV", "development") == "development" else None,
    env_file_encoding="utf-8",
    extra="allow"
  )

  # Supabase creds
  supabase_url: SecretStr | None = None
  supabase_key: SecretStr | None = None

  # OpenAI creds
  openai_api_key: SecretStr | None = None

  # General settings
  env: SecretStr | None = None

  # Praw creds
  client_id: SecretStr | None = None
  client_secret: SecretStr | None = None

  # Praw settings
  CODE_ENVIRONMENT: str = "python"
  TITLE: str = "Leaddits"
  VERSION: str = "1.0.0"
  REDDIT_USERNAME: str = "Icy_Pie_3434"
  USER_AGENT: str = f"{CODE_ENVIRONMENT}:{TITLE}:{VERSION} (by u/{REDDIT_USERNAME})"
  IS_READ_ONLY: bool = True
  TIMEOUT: int = 60

configs = Configs()
