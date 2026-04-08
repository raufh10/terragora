package botserver

import (
  "context"
  "fmt"
  "log"
  "os"
  "strings"
  "time"

  "github.com/openai/openai-go/v3"
  llm "leaddits/internal/pkg/llm"
  pg "leaddits/internal/pkg/pg"
)

// GetMarketplaceReply handles the full pipeline: Embedding -> DB -> LLM -> Formatting
func GetMarketplaceReply(ctx context.Context, text string, llmClient *openai.Client) string {
  userQuery := strings.TrimSpace(text)
  if userQuery == "" {
    return "⚠️ What used item are you looking for today?"
  }

  // 1. Initialize DB Connection using the new pg package logic
  dbConn := os.Getenv("DATABASE_URL")
  db, err := pg.Connect(dbConn)
  if err != nil {
    log.Printf("DB Connection Error: %v", err)
    return "❌ Database connection issue. Please try again later."
  }
  defer db.Close()

  // 2. 🔍 Get Embedding
  embedCtx, cancelEmbed := context.WithTimeout(ctx, 10*time.Second)
  defer cancelEmbed()

  queryVector, err := llm.GetEmbedding(embedCtx, userQuery)
  if err != nil || len(queryVector) == 0 {
    log.Printf("Embedding Error: %v", err)
    return "❌ Sorry, I had trouble processing your search. Please try again."
  }

  // 3. 🗄️ Fetch from DB using the refactored pg.FetchRelevantPosts
  relevantPosts, err := pg.FetchRelevantPosts(db, queryVector, 5)
  if err != nil {
    log.Printf("DB Fetch Error: %v", err)
    return "❌ Database query failed. Please try again later."
  }

  if len(relevantPosts) == 0 {
    return "🔍 No matching items found. Try a different keyword!"
  }

  // 4. 🧠 LLM Analysis
  llmCtx, cancelLLM := context.WithTimeout(ctx, 30*time.Second)
  defer cancelLLM()

  var contextParts []string
  for _, p := range relevantPosts {
    content := "No content"
    if p.Content != nil {
      content = *p.Content
    }
    url := "No URL"
    if p.URL != nil {
      url = *p.URL
    }
    contextParts = append(contextParts, fmt.Sprintf("Title: %s\nContent: %s\nURL: %s", p.Title, content, url))
  }
  contextText := strings.Join(contextParts, "\n---\n")

  const systemPrompt = `You are Terragora, an AI marketplace scout. Your task is to analyze raw marketplace posts and extract only high-quality 'WTS' (Want To Sell) listings that match the user's intent.

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
- Higher score = better confidence and value.`

  searchTask := llm.NewStructuredTask[llm.MarketplaceSearch]("terragora_scout", systemPrompt)

  result, err := llm.SearchUsedItems(llmCtx, llmClient, searchTask, userQuery, contextText)
  if err != nil || result == nil || len(result.Listings) == 0 {
    log.Printf("LLM Analysis Error: %v", err)
    return "❌ I couldn't find any valid 'For Sale' listings for that item right now."
  }

  // 5. 🧾 Format final Telegram message
  return FormatTelegramMessage(userQuery, result, relevantPosts)
}

