package pkg

import (
  "encoding/json"
  "time"

  "github.com/google/uuid"
)

// StorablePost represents the raw data coming from the scraper
type StorablePost struct {
  RedditID string                 `json:"reddit_id"`
  Title    string                 `json:"title"`
  Content  string                 `json:"content"`
  URL      string                 `json:"url"`
  PostedAt float64                `json:"posted_at"`
  Metadata map[string]interface{} `json:"metadata"`
  IsActive bool                   `json:"is_active"`
}

// RedditPost maps directly to your public.reddit_posts schema for reading
type RedditPost struct {
  ID          uuid.UUID       `db:"id"`
  RedditID    string          `db:"reddit_id"`
  SubredditID *int            `db:"subreddit_id"`
  Title       string          `db:"title"`
  Content     *string         `db:"content"`
  URL         *string         `db:"url"`
  Price       json.RawMessage `db:"price"`
  PostedAt    *time.Time      `db:"posted_at"`
  ScrapedAt   time.Time       `db:"scraped_at"`
  Metadata    json.RawMessage `db:"metadata"`
  IsActive    bool            `db:"is_active"`
  Notes       *string         `db:"notes"`
  Similarity  float64         `db:"similarity"`
}
