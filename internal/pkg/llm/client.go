package llm

import (
  "time"

  "github.com/openai/openai-go/v3"
  "github.com/openai/openai-go/v3/option"
)

const (
  MaxRetries = 2
  RetryDelay = 1 * time.Second
)

// NewClient initializes a new OpenAI client.
func NewClient(apiKey string) *openai.Client {
  client := openai.NewClient(option.WithAPIKey(apiKey))
  return client
}

