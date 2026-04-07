package botserver

import (
  "context"
  "encoding/json"
  "fmt"
  "log"
  "strings"
  "time"

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
      Model:      openai.String(string(openai.EmbeddingModelTextEmbedding3Small)),
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
      Model: openai.F("gpt-5.4-mini-2026-03-17"),
      Input: openai.F([]responses.ResponseNewParamsInputUnion{
        responses.ResponseNewParamsInput{
          Type: openai.F(responses.ResponseNewParamsInputTypeItem),
          Item: openai.F(responses.ResponseNewParamsInputItem{
            Type: openai.F(responses.ResponseNewParamsInputItemTypeMessage),
            Message: openai.F(responses.ResponseNewParamsInputItemMessage{
              Role: openai.F(responses.ResponseNewParamsInputItemMessageRoleUser),
              Content: openai.F([]responses.ResponseNewParamsInputItemMessageContentUnion{
                responses.ResponseNewParamsInputItemMessageContentText{
                  Type: openai.F(responses.ResponseNewParamsInputItemMessageContentTextTypeLines),
                  Text: openai.F(fmt.Sprintf("%s\n\nUser Search: %s\n\nContext:\n%s", 
                    GlobalConfig.MarketplaceSearchPrompt, userQuery, contextText)),
                },
              }),
            }),
          }),
        },
      }),
      // Using ResponseTextConfig based on your second screenshot
      Text: openai.F(responses.ResponseTextConfigParam{
        // Using ResponseFormatTextJSONSchemaConfig based on your first screenshot
        Format: openai.F[responses.ResponseFormatTextConfigUnion](
          responses.ResponseFormatTextJSONSchemaConfigParam{
            Type: openai.F(responses.ResponseFormatTextJSONSchemaConfigTypeJSONSchema),
            JSONSchema: openai.F(responses.ResponseFormatTextJSONSchemaConfigJSONSchemaParam{
              Name:        openai.String("MarketplaceSearch"),
              Description: openai.String("Structured marketplace listings"),
              Schema:      openai.F(MarketplaceSearch{}), // Struct converted to map[string]any by SDK
              Strict:      openai.Bool(true),
            }),
          },
        ),
      }),
    })

    if err == nil {
      var result MarketplaceSearch
      // Convienence method to grab the text from the response object
      outputText := resp.OutputText()
      
      err = json.Unmarshal([]byte(outputText), &result)
      if err != nil {
        return nil, fmt.Errorf("failed to unmarshal JSON: %w", err)
      }
      return &result, nil
    }

    log.Printf("⚠️ Responses API failed (attempt %d): %v", i+1, err)
    time.Sleep(RetryDelay)
  }

  return nil, fmt.Errorf("LLM search failed after retries")
}
