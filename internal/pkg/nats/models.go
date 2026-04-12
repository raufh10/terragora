package pkg

import "encoding/json"

type ScraperEvent struct {
  Pages     int    `json:"pages"`
  Limit     int    `json:"limit"`
  Target    string `json:"target"`
  Timestamp string `json:"timestamp"`
}

type PipelineEvent struct {
  ID        string `json:"id"`
  RedditID  string `json:"reddit_id"`
  Title     string `json:"title"`
  IsActive  bool   `json:"is_active"`

  // Optional fields use pointers to handle NULLs from Postgres/NATS
  Content   *string         `json:"content,omitempty"`
  URL       *string         `json:"url,omitempty"`
  PostedAt  *string         `json:"posted_at,omitempty"`
  ScrapedAt *string         `json:"scraped_at,omitempty"`
  Notes     *string         `json:"notes,omitempty"`

  // Complex types use RawMessage or maps
  Metadata  json.RawMessage `json:"metadata,omitempty"`
  Price     json.RawMessage `json:"price,omitempty"`     // Since price is jsonb
  Embedding []float32       `json:"embedding,omitempty"` // vector(1536) maps to float slice
}

