package filters

import (
  "context"
  "fmt"
  llmPkg "leaddits/internal/pkg/llm"
)

// ExtractionClient defines the interface needed for product data extraction.
// This decouples the filter from the specific LLM implementation.
type ExtractionClient interface {
  ExtractProduct(ctx context.Context, text string) (*llmPkg.ProductExtraction, error)
}

// ExtractProductDetails calls the provided client to get structured prices and notes.
func ExtractProductDetails(ctx context.Context, client ExtractionClient, payload *ExtractionPayload) error {
  if payload.CleanedText == "" {
    return fmt.Errorf("cannot extract details from empty text")
  }

  extracted, err := client.ExtractProduct(ctx, payload.CleanedText)
  if err != nil {
    return fmt.Errorf("extraction failed: %w", err)
  }

  if extracted == nil {
    return fmt.Errorf("extraction returned nil result")
  }

  payload.Extraction = *extracted
  return nil
}

