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

  # Telegram creds
  telegram_bot_token: SecretStr | None = None
  telegram_webhook_url: SecretStr | None = None
  telegram_webhook_secret: SecretStr | None = None
  notification_telegram_bot_token: SecretStr | None = None
  notification_telegram_user_id: SecretStr | None = None

  # OpenAI creds
  openai_api_key: SecretStr | None = None

  # pgvector creds
  conn_str: SecretStr | None = None

  # General settings
  env: SecretStr | None = None

  # OpenAI settings
  MarketplaceSearchPrompt: str = """
    You are Terragora, an AI marketplace scout. Your task is to analyze raw marketplace posts and extract only high-quality 'WTS' (Want To Sell) listings that match the user's intent.

    STRICT RULES:
    - Only include WTS (selling) posts. Completely ignore WTB, discussions, or unclear posts.
    - Do not invent or assume missing data. If information is not present, omit it or use null where allowed.
    - Extract and condense seller notes into a maximum of 3 short bullet points per listing.
    - Keep each note factual, specific, and scannable (no long sentences, no filler words).
    - Infer condition only if clearly stated or strongly implied; otherwise keep it generic.

    QUALITY FILTERING:
    - Prioritize listings with clear details, fewer risks, and better overall value signals.
    - Down-rank or exclude listings with vague descriptions, missing key info, or suspicious wording.
    - Highlight risks explicitly in 'watch_out'.

    SCORING:
    - Assign a deal_score from 0–10 based on condition clarity, completeness, and risk level.
    - Higher score = better confidence and value.
  """

configs = Configs()
