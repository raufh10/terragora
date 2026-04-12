package llm

import (
  "context"
  "encoding/json"
  "fmt"
  "log"
  "time"

  "github.com/openai/openai-go/v3"
  "github.com/openai/openai-go/v3/responses"
)

func SearchUsedItems(ctx context.Context, client *openai.Client, task StructuredTask, userQuery string, contextText string) (*MarketplaceSearch, error) {
  
  fullInput := fmt.Sprintf("%s\n\nUser Query: %s\n\nContext:\n%s", 
    task.SystemPrompt, userQuery, contextText)

  for i := 0; i < MaxRetries; i++ {
    data, err := callOpenAIWithSchema(ctx, client, fullInput, task.Name, task.Schema)
    
    if err == nil {
      var result MarketplaceSearch
      if err := json.Unmarshal(data, &result); err != nil {
        return nil, fmt.Errorf("unmarshal failed: %w", err)
      }
      return &result, nil
    }

    log.Printf("⚠️ %s failed (attempt %d): %v", task.Name, i+1, err)

    select {
    case <-time.After(RetryDelay):
    case <-ctx.Done():
      return nil, ctx.Err()
    }
  }

  return nil, fmt.Errorf("task %s failed after retries", task.Name)
}

func callOpenAIWithSchema(ctx context.Context, client *openai.Client, input string, schemaName string, schema map[string]any) ([]byte, error) {
  resp, err := client.Responses.New(ctx, responses.ResponseNewParams{
    Model: openai.ChatModelGPT4oMini,
    Input: responses.ResponseNewParamsInputUnion{
      OfString: openai.String(input),
    },
    Text: responses.ResponseTextConfigParam{
      Format: responses.ResponseFormatTextConfigParamOfJSONSchema(
        schemaName,
        schema,
      ),
    },
  })

  if err != nil {
    return nil, err
  }

  return []byte(resp.OutputText()), nil
}
