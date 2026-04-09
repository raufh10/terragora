package filters

import (
  "context"
  "fmt"
)

// EmbeddingClient defines the interface needed to generate vectors.
type EmbeddingClient interface {
  CreateEmbedding(ctx context.Context, input string) ([]float32, error)
}

// GenerateEmbedding takes the assembled text and populates the Payload with a vector.
func GenerateEmbedding(ctx context.Context, client EmbeddingClient, payload *VectorizationPayload, assembledText string) error {
  if assembledText == "" {
    return fmt.Errorf("cannot generate embedding for empty string")
  }

  vector, err := client.CreateEmbedding(ctx, assembledText)
  if err != nil {
    return fmt.Errorf("embedding generation failed: %w", err)
  }

  payload.Embedding = vector
  return nil
}
