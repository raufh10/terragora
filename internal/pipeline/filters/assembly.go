package filters

import (
  "fmt"
)

// AssembleEmbeddingText creates the final string used to generate the vector embedding.
func AssembleEmbeddingText(payload *VectorizationPayload, category string, formattedPrice string) string {
  return fmt.Sprintf(
    "Category: %s | Product: %s | Price: %s | Info: %s",
    category,
    payload.Post.Title,
    formattedPrice,
    payload.Post.Notes,
  )
}
