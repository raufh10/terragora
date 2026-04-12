package pipeline

import (
  pg "leaddits/internal/pkg/pg"
  llm "leaddits/internal/pkg/llm"
)

// ExtractionPayload carries state through the LLM data extraction pipeline.
// Flow: Merge -> Clean -> Extract -> Prepare -> DB Update
type ExtractionPayload struct {
  Post        pg.RedditPost          // Input: Raw DB row
  FullText    string                 // Title + Content merged
  CleanedText string                 // Noise removed for LLM consumption
  Extraction  llm.ProductExtraction // Output: Structured prices and notes
}

// VectorizationPayload carries state through the Embedding generation pipeline.
// Flow: Category -> Price -> Assembly -> Vectorize -> DB Update
type VectorizationPayload struct {
  Post           pg.RedditPost // Input: Row (must have Price and Notes populated)
  Category       string        // Extracted from metadata flairs
  FormattedPrice string        // Human-readable price (e.g., Rp 1.500.000)
  AssembledText  string        // Final string: "Category: ... | Product: ..."
  Embedding      []float32     // Output: 1536-dimensional vector
}
