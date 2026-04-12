package security

import (
  "net/http"
  "os"
)

// AuthenticateRequest checks the Telegram Secret Token against the environment variable.
func AuthenticateRequest(r *http.Request) bool {
  secret := r.Header.Get("X-Telegram-Bot-Api-Secret-Token")
  expectedSecret := os.Getenv("TELEGRAM_WEBHOOK_SECRET")
  
  if expectedSecret == "" {
    return false
  }
  
  return secret != "" && secret == expectedSecret
}
