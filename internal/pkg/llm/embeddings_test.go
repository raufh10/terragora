package llm

import (
  "context"
  "testing"
)

func TestGetEmbedding_EmptyInput(t *testing.T) {
  // We can test the error handling of the function 
  // without needing a mock server for simple logic checks.
  ctx := context.Background()
  client := NewClient("fake-key")

  t.Run("Fails on invalid client/key", func(t *testing.T) {
    _, err := GetEmbedding(ctx, client, "test text")
    if err == nil {
      t.Error("expected error from invalid API key, got nil")
    }
  })
}

