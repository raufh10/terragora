package llm

// PriceRange represents a fixed price or a numeric span.
type PriceRange struct {
  Start *float64 `json:"start" jsonschema_description:"The fixed price or the lower bound of a range."`
  Max   *float64 `json:"max" jsonschema_description:"The upper bound of a price range if provided."`
}

// ProductExtraction represents structured data extracted from a raw post.
type ProductExtraction struct {
  Prices []PriceRange `json:"prices" jsonschema_description:"List of prices or price ranges extracted (e.g., {'start': 100000, 'max': 150000})."`
  Notes  string       `json:"notes" jsonschema_description:"1-3 sentences of additional context regarding condition, location, or bundle details."`
}
