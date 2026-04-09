package filters

import (
  "context"
  "fmt"
  llm "leaddits/internal/pkg/llm"
  "leaddits/internal/pipeline"
)

func ExtractProductDetails(ctx context.Context, llmClient llm.Client, payload *pipeline.PipelinePayload) error {

  extracted, err := llmClient.ExtractProduct(ctx, payload.CleanedText)
  if err != nil {
    return fmt.Errorf("extraction failed: %w", err)
  }

  payload.Extraction = *extracted
  return nil
}

