package botserver

import (
  "context"
  "log"
  "strings"
  "time"

  "leaddits/internal/pkg"
)

// GetMarketplaceReply handles the full pipeline: Embedding -> DB -> LLM -> Formatting
func GetMarketplaceReply(ctx context.Context, text string) string {
  userQuery := strings.TrimSpace(text)
  if userQuery == "" {
    return "⚠️ What used item are you looking for today?"
  }

  // 1. Initialize DB Connection (Usually passed in or managed via a singleton)
  db, err := pkg.Connect(GlobalConfig.ConnStr)
  if err != nil {
    log.Printf("DB Connection Error: %v", err)
    return "❌ Database connection issue. Please try again later."
  }
  defer db.Close()

  // 2. 🔍 Get Embedding
  // We wrap this in a timeout to prevent long hangs
  embedCtx, cancelEmbed := context.WithTimeout(ctx, 10*time.Second)
  defer cancelEmbed()

  queryVector, err := GetEmbedding(embedCtx, userQuery)
  if err != nil || len(queryVector) == 0 {
    log.Printf("Embedding Error: %v", err)
    return "❌ Sorry, I had trouble processing your search. Please try again."
  }

  // 3. 🗄️ Fetch from DB
  relevantPosts, err := pkg.FetchRelevantPosts(db, queryVector, 5)
  if err != nil {
    log.Printf("DB Fetch Error: %v", err)
    return "❌ Database query failed. Please try again later."
  }

  if len(relevantPosts) == 0 {
    return "🔍 No matching items found. Try a different keyword!"
  }

  // 4. 🧠 LLM Analysis
  // Convert pkg.RedditPost to a generic map if your SearchUsedItems still expects map[string]interface{}
  // Or update SearchUsedItems to accept []pkg.RedditPost (Recommended)
  llmCtx, cancelLLM := context.WithTimeout(ctx, 30*time.Second)
  defer cancelLLM()

  // We convert the posts to a compatible slice for the LLM function
  postsMap := make([]map[string]interface{}, len(relevantPosts))
  for i, p := range relevantPosts {
    postsMap[i] = map[string]interface{}{
      "title":   p.Title,
      "content": p.Content,
      "price":   p.Price,
    }
  }

  result, err := SearchUsedItems(llmCtx, userQuery, postsMap)
  if err != nil || result == nil || len(result.Listings) == 0 {
    log.Printf("LLM Analysis Error: %v", err)
    return "❌ Failed to analyze results. Try a more specific search."
  }

  // 5. 🧾 Format final Telegram message
  reply := FormatTelegramMessage(userQuery, result, relevantPosts)
  
  return reply
}

