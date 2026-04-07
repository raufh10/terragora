package main

import (
  "bytes"
  "context"
  "encoding/json"
  "fmt"
  "io"
  "net/http"
  "os"
  "strings"
  "sync"
  "time"

  // Replace 'leaddits' with the module name found in your go.mod file
  "leaddits/internal/bot-server" 
)

var (
  lastSeen = make(map[int64]float64)
  mu       sync.Mutex 
)

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
  // Accessing TelegramBotToken from the imported botserver package
  url := fmt.Sprintf("https://api.telegram.org/bot%s/sendMessage", botserver.GlobalConfig.TelegramBotToken)
  payload, _ := json.Marshal(map[string]interface{}{
    "chat_id":    chatID,
    "text":       text,
    "parse_mode": "Markdown",
  })
  http.Post(url, "application/json", bytes.NewBuffer(payload))
}

func sendChatAction(chatID int64, action string) {
  url := fmt.Sprintf("https://api.telegram.org/bot%s/sendChatAction", botserver.GlobalConfig.TelegramBotToken)
  payload, _ := json.Marshal(map[string]interface{}{
    "chat_id": chatID,
    "action":  action,
  })
  http.Post(url, "application/json", bytes.NewBuffer(payload))
}

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
  // Verify Secret Token using the botserver package prefix
  secret := r.Header.Get("X-Telegram-Bot-Api-Secret-Token")
  if secret != botserver.GlobalConfig.TelegramWebhookSecret {
    w.WriteHeader(http.StatusUnauthorized)
    return
  }

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

  text := strings.TrimSpace(rawText)
  if len(text) > 1000 {
    text = text[:1000]
  }
  text = strings.Join(strings.Fields(text), " ")

  if strings.Count(text, "http") > 3 {
    sendMessage(chatID, "🚫 Too many links in message.")
    return
  }

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

  ctx, cancel := context.WithCancel(r.Context())
  go typingLoop(ctx, chatID)
  defer cancel()

  // Calling GetMarketplaceReply from the internal package
  replyText := botserver.GetMarketplaceReply(ctx, text)
  sendMessage(chatID, replyText)

  w.WriteHeader(http.StatusOK)
  fmt.Fprint(w, `{"status": "ok"}`)
}

func main() {
  // Initialize config from the internal package
  botserver.LoadConfig()

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

