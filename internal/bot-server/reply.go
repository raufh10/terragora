package botserver

import (
  "context"
  "log"
  "os"
  "strings"
  "time"

  "github.com/openai/openai-go/v3"
  llm "leaddits/internal/pkg/llm"
  pg "leaddits/internal/pkg/pg"
)

// GetMarketplaceReply handles the pipeline: Embedding -> DB -> Formatting
func GetMarketplaceReply(ctx context.Context, text string, llmClient *openai.Client) string {
  userQuery := strings.TrimSpace(text)
  if userQuery == "" {
    return "⚠️ What used item are you looking for today?"
  }

  // 1. Initialize DB Connection
  dbConn := os.Getenv("DATABASE_URL")
  db, err := pg.Connect(dbConn)
  if err != nil {
    log.Printf("DB Connection Error: %v", err)
    return "❌ Database connection issue. Please try again later."
  }
  defer db.Close()

  // 2. 🔍 Get Embedding (Used for semantic vector search)
  embedCtx, cancelEmbed := context.WithTimeout(ctx, 10*time.Second)
  defer cancelEmbed()

  queryVector, err := llm.GetEmbedding(embedCtx, llmClient, userQuery)
  if err != nil || len(queryVector) == 0 {
    log.Printf("Embedding Error: %v", err)
    return "❌ Sorry, I had trouble processing your search. Please try again."
  }

  // 3. 🗄️ Fetch from DB using vector similarity
  relevantPosts, err := pg.FetchRelevantPosts(db, queryVector, 5)
  if err != nil {
    log.Printf("DB Fetch Error: %v", err)
    return "❌ Database query failed. Please try again later."
  }

  if len(relevantPosts) == 0 {
    return "🔍 No matching items found. Try a different keyword!"
  }

  // 4. 🧾 Format final Telegram message directly from DB results
  return FormatTelegramMessage(userQuery, relevantPosts)
}
