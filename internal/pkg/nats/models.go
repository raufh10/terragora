package pkg

type ScraperEvent struct {
  Pages     int    `json:"pages"`
  Limit     int    `json:"limit"`
  Target    string `json:"target"`
  Timestamp string `json:"timestamp"`
}

type PipelineEvent struct {
  ID         string                 `json:"id"`
  RedditID   string                 `json:"reddit_id"`
  Title      string                 `json:"title"`
  Content    string                 `json:"content"`
  URL        string                 `json:"url"`
  PostedAt   string                 `json:"posted_at"`
  ScrapedAt  string                 `json:"scraped_at"`
  Metadata   map[string]interface{} `json:"metadata"`
  IsActive   bool                   `json:"is_active"`
}
