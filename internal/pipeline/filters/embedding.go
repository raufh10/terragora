package filters

import (
  "context"
  "fmt"
)

// 1. LOCAL INTERFACE
type EmbeddingClient interface {
  CreateEmbedding(ctx context.Context, input string) ([]float32, error)
}

// 2. THE FILTER LOGIC
func GenerateEmbedding(ctx context.Context, client EmbeddingClient, payload *VectorizationPayload, assembledText string) error {
  if assembledText == "" {
    return fmt.Errorf("cannot generate embedding for empty string")
  }

  // Direct call to the client's CreateEmbedding method.
  vector, err := client.CreateEmbedding(ctx, assembledText)
  if err != nil {
    return fmt.Errorf("embedding generation failed: %w", err)
  }

  if vector == nil {
    return fmt.Errorf("embedding service returned nil vector")
  }

  payload.Embedding = vector
  return nil
}
