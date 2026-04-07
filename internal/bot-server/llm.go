package botserver

import (
  "context"
  "encoding/json"
  "fmt"
  "log"
  "strings"
  "time"

  "github.com/invopop/jsonschema"
  "github.com/openai/openai-go/v3"
  "github.com/openai/openai-go/v3/option"
  "github.com/openai/openai-go/v3/responses"
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
      Input: openai.EmbeddingNewParamsInputUnion{
        OfString: openai.String(text),
      },
      Model:      openai.EmbeddingModelTextEmbedding3Small,
      Dimensions: openai.Int(1536),
    })

    if err == nil {
      if len(res.Data) == 0 {
        return nil, fmt.Errorf("empty embedding data returned")
      }
      embeddings := make([]float32, len(res.Data[0].Embedding))
      for j, v := range res.Data[0].Embedding {
        embeddings[j] = float32(v)
      }
      return embeddings, nil
    }

    log.Printf("⚠️ Embedding failed (attempt %d): %v", i+1, err)
    time.Sleep(RetryDelay)
  }
  return nil, fmt.Errorf("failed after %d retries", MaxRetries)
}

// GenerateSchema follows the provided documentation example for Structured Outputs
func GenerateSchema[T any]() map[string]any {
  reflector := jsonschema.Reflector{
    AllowAdditionalProperties: false,
    DoNotReference:            true,
  }
  var v T
  schema := reflector.Reflect(v)

  data, _ := json.Marshal(schema)
  var result map[string]any
  json.Unmarshal(data, &result)
  return result
}

// Global schema generated at initialization
var MarketplaceSearchSchema = GenerateSchema[MarketplaceSearch]()

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

  client := openai.NewClient(option.WithAPIKey(GlobalConfig.OpenAIAPIKey))

  for i := 0; i < MaxRetries; i++ {
    resp, err := client.Responses.New(ctx, responses.ResponseNewParams{
      Model: openai.ChatModelGPT5_4Mini,
      // Using the OfString helper as seen in the example main()
      Input: responses.ResponseNewParamsInputUnion{
        OfString: openai.String(fmt.Sprintf("%s\n\nUser Search: %s\n\nContext:\n%s", 
          GlobalConfig.MarketplaceSearchPrompt, userQuery, contextText)),
      },
      Text: responses.ResponseTextConfigParam{
        // Using the helper from your example: FormatTextConfigParamOfJSONSchema
        Format: responses.ResponseFormatTextConfigParamOfJSONSchema(
          "marketplace_search",
          MarketplaceSearchSchema,
        ),
      },
    })

    if err == nil {
      var result MarketplaceSearch
      // Extracting into the well-typed struct
      err = json.Unmarshal([]byte(resp.OutputText()), &result)
      if err != nil {
        return nil, fmt.Errorf("failed to unmarshal JSON: %w", err)
      }
      return &result, nil
    }

    log.Printf("⚠️ Responses API failed (attempt %d): %v", i+1, err)
    
    select {
    case <-time.After(RetryDelay):
    case <-ctx.Done():
      return nil, ctx.Err()
    }
  }

  return nil, fmt.Errorf("LLM search failed after retries")
}
