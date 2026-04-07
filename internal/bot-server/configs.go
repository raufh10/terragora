package botserver

import (
  "log"
  "os"

  "github.com/caarlos0/env/v10"
  "github.com/joho/godotenv"
)

type Configs struct {
  // Supabase creds
  SupabaseURL string `env:"SUPABASE_URL"`
  SupabaseKey string `env:"SUPABASE_KEY"`

  // Telegram creds
  TelegramBotToken             string `env:"TELEGRAM_BOT_TOKEN"`
  TelegramWebhookURL           string `env:"TELEGRAM_WEBHOOK_URL"`
  TelegramWebhookSecret        string `env:"TELEGRAM_WEBHOOK_SECRET"`
  NotificationTelegramBotToken string `env:"NOTIFICATION_TELEGRAM_BOT_TOKEN"`
  NotificationTelegramUserID   string `env:"NOTIFICATION_TELEGRAM_USER_ID"`

  // OpenAI creds
  OpenAIAPIKey string `env:"OPENAI_API_KEY"`

  // pgvector creds
  ConnStr string `env:"CONN_STR"`

  // General settings
  Env string `env:"ENV" envDefault:"development"`

  // OpenAI settings (Hardcoded constants as in your Python version)
  MarketplaceSearchPrompt string
}

var GlobalConfig Configs

func LoadConfig() {
  // 1. Load .env file if in development
  envMode := os.Getenv("ENV")
  if envMode == "" || envMode == "development" {
    err := godotenv.Load(".env")
    if err != nil {
      log.Println("No .env file found, falling back to system environment variables")
    }
  }

  // 2. Parse environment variables into struct
  cfg := Configs{}
  if err := env.Parse(&cfg); err != nil {
    log.Fatalf("Failed to parse env vars: %v", err)
  }

  // 3. Set the hardcoded prompt
  cfg.MarketplaceSearchPrompt = `
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
  `

  GlobalConfig = cfg
}

