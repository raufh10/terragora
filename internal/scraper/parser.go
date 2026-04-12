package scraper

import (
  "encoding/json"
  "strings"

  // We alias it to 'pg' for clarity, otherwise you'd use 'pkg.StorablePost'
  pg "leaddits/internal/pkg/pg" 
)

func ProcessResponse(resp RedditResponse) []pg.StorablePost {
  posts := make([]pg.StorablePost, 0, len(resp.Data.Children))

  for _, child := range resp.Data.Children {
    data := child.Data
    isActive := hasWTSFlair(data.LinkFlairRichText)

    var metadata map[string]interface{}
    rawBytes, err := json.Marshal(data)
    if err == nil {
      _ = json.Unmarshal(rawBytes, &metadata)
    }

    posts = append(posts, pg.StorablePost{
      RedditID: data.RedditID,
      Title:    data.Title,
      Content:  data.Selftext,
      URL:      data.URL,
      PostedAt: data.CreatedUTC,
      Metadata: metadata,
      IsActive: isActive,
    })
  }

  return posts
}

func hasWTSFlair(flairs []map[string]interface{}) bool {
  for _, flair := range flairs {
    if val, ok := flair["t"]; ok {
      if text, ok := val.(string); ok {
        if strings.Contains(strings.ToUpper(text), "WTS") {
          return true
        }
      }
    }
  }
  return false
}
