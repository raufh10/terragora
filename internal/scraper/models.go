package scraper

import "time"

// UserAgent represents a browser identity and its operating system.
type UserAgent struct {
  Raw  string `json:"str"`
  Type string `json:"type"` // windows, macos, linux, android, ios
}

// Targets holds the URLs and subreddits for the scraper.
type Targets struct {
  BaseURL    string
  Subreddits []string
}

// ScraperConfigs holds the technical settings for the scraper instance.
type ScraperConfigs struct {
  UserAgentPool  []UserAgent
  LastUsedUA     string
  ProxyURL       string
  TimeoutSeconds time.Duration
}

// Client is the main scraper controller.
type Client struct {
  DatabaseURL string
  Targets     Targets
  Config      ScraperConfigs
}

// --- Reddit Specific API Models ---

type RedditPostData struct {
  RedditID          string                   `json:"name"`
  Title             string                   `json:"title"`
  Selftext          string                   `json:"selftext"`
  URL               string                   `json:"url"`
  Subreddit         string                   `json:"subreddit"`
  CreatedUTC        float64                  `json:"created_utc"`
  LinkFlairRichText []map[string]interface{} `json:"link_flair_richtext"`
}

type RedditPostChild struct {
  Data RedditPostData `json:"data"`
}

type RedditData struct {
  Children []RedditPostChild `json:"children"`
  After    *string           `json:"after"`
}

type RedditResponse struct {
  Data RedditData `json:"data"`
}

type StorablePost struct {
  RedditID string                 `json:"reddit_id"`
  Title    string                 `json:"title"`
  Content  string                 `json:"content"`
  URL      string                 `json:"url"`
  PostedAt float64                `json:"posted_at"`
  Metadata map[string]interface{} `json:"metadata"`
  IsActive bool                   `json:"is_active"`
}
