package filters

import (
  "fmt"
)

// AssembleEmbeddingText creates the final string used to generate the vector embedding.
func AssembleEmbeddingText(payload *VectorizationPayload, category string, formattedPrice string) string {
  return fmt.Sprintf(
    "Category: %s | Product: %s | Info: %s",
    category,
    payload.Post.Title,
    payload.Post.Notes,
  )
}

