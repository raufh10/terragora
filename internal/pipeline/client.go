package pipeline

import (
  "context"
  llmPkg "leaddits/internal/pkg/llm"
)

// Client defines the interface the pipeline engine needs.
// This allows the engine to remain agnostic of the actual LLM implementation.
type Client interface {
  ExtractProduct(ctx context.Context, text string) (*llmPkg.ProductExtraction, error)
  CreateEmbedding(ctx context.Context, input string) ([]float32, error)
}

// clientWrapper wraps the existing raw OpenAI client to satisfy the Client interface.
type clientWrapper struct {
  api interface {
    ExtractProduct(ctx context.Context, text string) (*llmPkg.ProductExtraction, error)
    CreateEmbedding(ctx context.Context, input string) ([]float32, error)
  }
}

// NewClientBridge wraps any object that satisfies the interface into a pipeline.Client
func NewClientBridge(rawClient interface{}) Client {
  // We cast the rawClient to our local interface
  return rawClient.(Client)
}
