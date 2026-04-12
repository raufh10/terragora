package botserver

import (
  "bytes"
  "context"
  "encoding/json"
  "fmt"
  "net/http"
  "os"
  "time"
)

// SendMessage sends a Markdown formatted message to Telegram
func SendMessage(chatID int64, text string) {
  token := os.Getenv("TELEGRAM_BOT_TOKEN")
  url := fmt.Sprintf("https://api.telegram.org/bot%s/sendMessage", token)

  payload, _ := json.Marshal(map[string]interface{}{
    "chat_id":    chatID,
    "text":       text,
    "parse_mode": "Markdown",
  })
  http.Post(url, "application/json", bytes.NewBuffer(payload))
}

// SendChatAction sends a status (like 'typing') to the user
func SendChatAction(chatID int64, action string) {
  token := os.Getenv("TELEGRAM_BOT_TOKEN")
  url := fmt.Sprintf("https://api.telegram.org/bot%s/sendChatAction", token)

  payload, _ := json.Marshal(map[string]interface{}{
    "chat_id": chatID,
    "action":  action,
  })
  http.Post(url, "application/json", bytes.NewBuffer(payload))
}

// TypingLoop continuously sends the typing status until the context is cancelled
func TypingLoop(ctx context.Context, chatID int64) {
  ticker := time.NewTicker(4 * time.Second)
  defer ticker.Stop()
  for {
    select {
    case <-ctx.Done():
      return
    case <-ticker.C:
      SendChatAction(chatID, "typing")
    }
  }
}

