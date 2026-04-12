package filters

import (
  "fmt"
  "leaddits/internal/pipeline"
)

// AssembleEmbeddingText creates the final string used to generate the vector embedding.
func AssembleEmbeddingText(payload *pipeline.PipelinePayload, category string, formattedPrice string) string {
  return fmt.Sprintf(
    "Category: %s | Product: %s | Price: %s | Info: %s",
    category,
    payload.Post.Title,
    formattedPrice,
    payload.Extraction.Notes,
  )
}

