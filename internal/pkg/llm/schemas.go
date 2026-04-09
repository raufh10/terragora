package llm

// Listing represents a single item found in the marketplace.
type Listing struct {
  Location    *string  `json:"location" jsonschema_description:"City where the item is located."`
  Condition   string   `json:"condition" jsonschema_description:"Condition of the item (e.g., 90%, like new, etc.)."`
  SellerNotes []string `json:"seller_notes" jsonschema_description:"Key bullet points from seller notes (max 3)."`
  Verdict     string   `json:"verdict" jsonschema_description:"Clear recommendation label."`
  WatchOut    string   `json:"watch_out" jsonschema_description:"Risk or warning. Use '-' if none."`
  DealScore   *float64 `json:"deal_score" jsonschema_description:"Optional score from 0–10."`
  URL         string   `json:"url" jsonschema_description:"Direct link to the listing."`
}

// MarketplaceSearch is the top-level container for structured outputs.
type MarketplaceSearch struct {
  Listings []Listing `json:"listings" jsonschema_description:"Top matching listings sorted by relevance."`
}

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
