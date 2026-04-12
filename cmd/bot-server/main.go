package main

import (
  "bytes"
  "context"
  "encoding/json"
  "fmt"
  "io"
  "net/http"
  "strings"
  "sync"
  "time"
)

var (
  lastSeen = make(map[int64]float64)
  mu       sync.Mutex // Protects the lastSeen map for concurrent access
)

// Telegram types for incoming webhook
type Update struct {
  Message struct {
    Chat struct {
      ID int64 `json:"id"`
    } `json:"chat"`
    From struct {
      Username string `json:"username"`
    } `json:"from"`
    Text string `json:"text"`
  } `json:"message"`
}

func sendMessage(chatID int64, text string) {
  url := fmt.Sprintf("https://api.telegram.org/bot%s/sendMessage", GlobalConfig.TelegramBotToken)
  payload, _ := json.Marshal(map[string]interface{}{
    "chat_id":    chatID,
    "text":       text,
    "parse_mode": "Markdown",
  })
  http.Post(url, "application/json", bytes.NewBuffer(payload))
}

func sendChatAction(chatID int64, action string) {
  url := fmt.Sprintf("https://api.telegram.org/bot%s/sendChatAction", GlobalConfig.TelegramBotToken)
  payload, _ := json.Marshal(map[string]interface{}{
    "chat_id": chatID,
    "action":  action,
  })
  http.Post(url, "application/json", bytes.NewBuffer(payload))
}

// typingLoop runs until the context is cancelled
func typingLoop(ctx context.Context, chatID int64) {
  ticker := time.NewTicker(4 * time.Second)
  defer ticker.Stop()
  for {
    select {
    case <-ctx.Done():
      return
    case <-ticker.C:
      sendChatAction(chatID, "typing")
    }
  }
}

func handleWebhook(w http.ResponseWriter, r *http.Request) {
  // 1. Verify Secret Token
  secret := r.Header.Get("X-Telegram-Bot-Api-Secret-Token")
  if secret != GlobalConfig.TelegramWebhookSecret {
    w.WriteHeader(http.StatusUnauthorized)
    return
  }

  // 2. Parse Body
  var update Update
  body, _ := io.ReadAll(r.Body)
  json.Unmarshal(body, &update)

  chatID := update.Message.Chat.ID
  if chatID == 0 {
    return
  }

  rawText := update.Message.Text
  if rawText == "" {
    sendMessage(chatID, "❌ I only support text messages for now.")
    return
  }

  // 3. Normalize & Constraints
  text := strings.TrimSpace(rawText)
  if len(text) > 1000 {
    text = text[:1000]
  }
  // Normalize whitespace
  text = strings.Join(strings.Fields(text), " ")

  // 4. Spam Guard
  if strings.Count(text, "http") > 3 {
    sendMessage(chatID, "🚫 Too many links in message.")
    return
  }

  // 5. Rate Limiting
  now := float64(time.Now().UnixNano()) / 1e9
  mu.Lock()
  last, exists := lastSeen[chatID]
  if exists && now-last < 1.0 {
    mu.Unlock()
    sendMessage(chatID, "⏳ You're sending messages too fast. Please slow down.")
    return
  }
  lastSeen[chatID] = now
  mu.Unlock()

  // 6. Process Reply
  // We use a context to manage the typing loop lifecycle
  ctx, cancel := context.WithCancel(context.Background())
  go typingLoop(ctx, chatID)
  defer cancel()

  // Get the reply from our orchestrator
  replyText := GetMarketplaceReply(ctx, text)
  sendMessage(chatID, replyText)

  w.WriteHeader(http.StatusOK)
  fmt.Fprint(w, `{"status": "ok"}`)
}

func main() {
  // Load config from our configs.go
  LoadConfig()

  http.HandleFunc("/webhook", handleWebhook)

  port := os.Getenv("PORT")
  if port == "" {
    port = "8080"
  }

  fmt.Printf("Bot server starting on :%s\n", port)
  if err := http.ListenAndServe(":"+port, nil); err != nil {
    panic(err)
  }
}

