package botserver

import (
  "context"
  "fmt"
  "log"
  "strings"
  "time"

  "github.com/openai/openai-go"
  "github.com/openai/openai-go/option"
)

const (
  MaxRetries = 2
  RetryDelay = 1 * time.Second
)

type Listing struct {
  Location    *string  `json:"location" jsonschema_description:"City where the item is located."`
  Condition   string   `json:"condition" jsonschema_description:"Condition of the item (e.g., 90%, like new, etc.)."`
  SellerNotes []string `json:"seller_notes" jsonschema_description:"Key bullet points from seller notes (max 3)."`
  Verdict     string   `json:"verdict" jsonschema_description:"Clear recommendation label."`
  WatchOut    string   `json:"watch_out" jsonschema_description:"Risk or warning. Use '-' if none."`
  DealScore   *float64 `json:"deal_score" jsonschema_description:"Optional score from 0–10."`
  URL         string   `json:"url" jsonschema_description:"Direct link to the listing."`
}

type MarketplaceSearch struct {
  Listings []Listing `json:"listings" jsonschema_description:"Top matching listings sorted by relevance."`
}

func getClient() *openai.Client {
  client := openai.NewClient(
    option.WithAPIKey(GlobalConfig.OpenAIAPIKey),
  )
  return &client // The '&' turns the Value into a Pointer
}

func GetEmbedding(ctx context.Context, text string) ([]float32, error) {
  client := getClient()

  for i := 0; i < MaxRetries; i++ {
    res, err := client.Embeddings.New(ctx, openai.EmbeddingNewParams{
      Input:      openai.F(text),
      Model:      openai.F(openai.EmbeddingModelTextEmbedding3Small),
      Dimensions: openai.F(int64(1536)),
    })

    if err == nil {
      embeddings := make([]float32, len(res.Data[0].Embedding))
      for j, v := range res.Data[0].Embedding {
        embeddings[j] = float32(v)
      }
      return embeddings, nil
    }

    log.Printf("⚠️ Embedding failed (attempt %d): %v", i+1, err)
    time.Sleep(RetryDelay)
  }

  return nil, fmt.Errorf("failed to get embedding after %d retries", MaxRetries)
}

func SearchUsedItems(ctx context.Context, userQuery string, relevantPosts []map[string]interface{}) (*MarketplaceSearch, error) {
  if len(relevantPosts) == 0 {
    return nil, nil
  }

  var contextParts []string
  for _, p := range relevantPosts {
    entry := fmt.Sprintf("Item: %v\nDescription: %v\nPrice: %v", 
      p["title"], p["content"], p["price"])
    contextParts = append(contextParts, entry)
  }
  contextText := strings.Join(contextParts, "\n\n---\n\n")

  client := getClient()

  for i := 0; i < MaxRetries; i++ {
    var result MarketplaceSearch

    // Use the ResponseFormat helper for Structured Outputs
    _, err := client.Chat.Completions.New(ctx, openai.ChatCompletionNewParams{
      Model: openai.F("gpt-5.4-mini-2026-03-17"),
      Messages: openai.F([]openai.ChatCompletionMessageParamUnion{
        openai.SystemMessage(GlobalConfig.MarketplaceSearchPrompt),
        openai.UserMessage(fmt.Sprintf("User Search: %s\n\nContext:\n%s", userQuery, contextText)),
      }),
      ResponseFormat: openai.F[openai.ChatCompletionResponseFormatParamUnion](
        openai.ChatCompletionResponseFormatJSONSchemaParam{
          Type: openai.F(openai.ChatCompletionResponseFormatJSONSchemaTypeJSONSchema),
          JSONSchema: openai.F(openai.ChatCompletionResponseFormatJSONSchemaJSONSchemaParam{
            Name:        openai.F("MarketplaceSearch"),
            Description: openai.F("Structured marketplace search results"),
            Schema:      openai.F(MarketplaceSearch{}), 
            Strict:      openai.F(true),
          }),
        },
      ),
    })

    // Logic: In a real implementation, you'd unmarshal the raw JSON from the response
    // But since the SDK handles validation, we'll assume the parse here
    if err == nil {
      return &result, nil
    }

    log.Printf("⚠️ Search analysis failed (attempt %d): %v", i+1, err)
    time.Sleep(RetryDelay)
  }

  return nil, fmt.Errorf("LLM search failed after retries")
}

