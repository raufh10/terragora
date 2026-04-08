package main

import (
  "context"
  "encoding/json"
  "fmt"
  "io"
  "net/http"
  "os"
  "sync"
  "time"

  "leaddits/internal/bot-server"
)

var (
  lastSeen = make(map[int64]float64)
  mu       sync.Mutex
)

func handleWebhook(w http.ResponseWriter, r *http.Request) {
  // 1. Auth check via direct env read
  secret := r.Header.Get("X-Telegram-Bot-Api-Secret-Token")
  expectedSecret := os.Getenv("TELEGRAM_WEBHOOK_SECRET")
  
  if secret == "" || secret != expectedSecret {
    w.WriteHeader(http.StatusUnauthorized)
    return
  }

  // 2. Decode Update
  var update botserver.Update
  body, _ := io.ReadAll(r.Body)
  json.Unmarshal(body, &update)

  chatID := update.Message.Chat.ID
  if chatID == 0 {
    return
  }

  // 3. Validation
  if update.Message.Text == "" {
    botserver.SendMessage(chatID, "❌ I only support text messages for now.")
    return
  }

  text := botserver.SanitizeInput(update.Message.Text)

  // 4. Rate Limiting
  now := float64(time.Now().UnixNano()) / 1e9
  mu.Lock()
  last, exists := lastSeen[chatID]
  if exists && now-last < 1.0 {
    mu.Unlock()
    botserver.SendMessage(chatID, "⏳ You're sending messages too fast.")
    return
  }
  lastSeen[chatID] = now
  mu.Unlock()

  // 5. Execution
  ctx, cancel := context.WithCancel(r.Context())
  go botserver.TypingLoop(ctx, chatID)
  defer cancel()

  // Note: Ensure your OpenAI client is initialized and passed here
  // replyText := botserver.GetMarketplaceReply(ctx, text, yourLLMClient)
  // For now, assuming standard flow:
  replyText := botserver.GetMarketplaceReply(ctx, text, nil) 
  botserver.SendMessage(chatID, replyText)

  w.WriteHeader(http.StatusOK)
  fmt.Fprint(w, `{"status": "ok"}`)
}

func main() {
  // No more botserver.LoadConfig() needed if using direct envs
  
  http.HandleFunc("/webhook", handleWebhook)

  port := os.Getenv("PORT")
  if port == "" { port = "8080" }

  fmt.Printf("Bot server starting on :%s\n", port)
  if err := http.ListenAndServe(":"+port, nil); err != nil {
    panic(err)
  }
}
