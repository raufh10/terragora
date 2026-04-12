package scraper

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
  After    *string           `json:"after"` // Pointer used for Nullable/Option
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

