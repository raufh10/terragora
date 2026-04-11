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

func callOpenAIWithSchema(ctx context.Context, client *openai.Client, input string, schemaName string, schema map[string]any) ([]byte, error) {
  resp, err := client.Responses.New(ctx, responses.ResponseNewParams{
    Model: openai.ChatModelGPT5_4Mini,
    ServiceTier: openai.String("flex"),
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
