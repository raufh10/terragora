package main

import (
  "context"
  "encoding/json"
  "fmt"
  "io"
  "net/http"
  "os"

  "github.com/openai/openai-go/v3"
  "leaddits/internal/bot-server"
  "leaddits/internal/bot-server/security"
  llm "leaddits/internal/pkg/llm"
)

func handleWebhook(w http.ResponseWriter, r *http.Request, client *openai.Client) {
  // 1. Auth check via security package
  if !security.AuthenticateRequest(r) {
    w.WriteHeader(http.StatusUnauthorized)
    return
  }

  // 2. Decode Update
  var update botserver.Update
  body, err := io.ReadAll(r.Body)
  if err != nil {
    return
  }
  if err := json.Unmarshal(body, &update); err != nil {
    return
  }

  chatID := update.Message.Chat.ID
  if chatID == 0 {
    return
  }

  // 3. Validation & Sanitization
  if update.Message.Text == "" {
    botserver.SendMessage(chatID, "❌ I only support text messages for now.")
    return
  }

  // Sanitize input with text-only check and length restriction
  text, err := security.SanitizeInput(update.Message.Text)
  if err != nil {
    botserver.SendMessage(chatID, fmt.Sprintf("⚠️ %v", err))
    return
  }

  // 4. Rate Limiting via security package
  if security.IsRateLimited(chatID) {
    botserver.SendMessage(chatID, "⏳ You're sending messages too fast. Please wait a moment.")
    return
  }

  // 5. Execution
  ctx, cancel := context.WithCancel(r.Context())
  go botserver.TypingLoop(ctx, chatID)
  defer cancel()

  // Get marketplace results via LLM
  replyText := botserver.GetMarketplaceReply(ctx, text, client)
  botserver.SendMessage(chatID, replyText)

  w.WriteHeader(http.StatusOK)
  fmt.Fprint(w, `{"status": "ok"}`)
}

func main() {
  apiKey := os.Getenv("OPENAI_API_KEY")
  if apiKey == "" {
    fmt.Println("CRITICAL: OPENAI_API_KEY is not set")
    os.Exit(1)
  }

  // Initializes the OpenAI client from your existing pkg/llm
  llmClient := llm.NewClient(apiKey)

  http.HandleFunc("/webhook", func(w http.ResponseWriter, r *http.Request) {
    handleWebhook(w, r, llmClient)
  })

  port := os.Getenv("PORT")
  if port == "" {
    port = "8080"
  }

  fmt.Printf("Bot server starting on :%s\n", port)
  if err := http.ListenAndServe(":"+port, nil); err != nil {
    panic(err)
  }
}

