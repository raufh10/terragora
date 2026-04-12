package filters

import (
  "context"
  "fmt"
  "leaddits/internal/pipeline"
)

// EmbeddingClient defines the interface needed to generate vectors.
// This allows you to swap between OpenAI, Cohere, or local models.
type EmbeddingClient interface {
  CreateEmbedding(ctx context.Context, input string) ([]float32, error)
}

// GenerateEmbedding takes the assembled text and populates the Payload with a vector.
func GenerateEmbedding(ctx context.Context, client EmbeddingClient, payload *pipeline.PipelinePayload, assembledText string) error {
  if assembledText == "" {
    return fmt.Errorf("cannot generate embedding for empty string")
  }

  // Call the embedding provider
  vector, err := client.CreateEmbedding(ctx, assembledText)
  if err != nil {
    return fmt.Errorf("embedding generation failed: %w", err)
  }

  // Store the vector in the payload for the final DB update
  payload.Embedding = vector
  return nil
}

