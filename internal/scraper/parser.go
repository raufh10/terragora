package scraper

import (
  "encoding/json"
  "strings"
)

// ProcessResponse converts a RedditResponse into a slice of StorablePosts.
// It replicates the Rust logic for checking "WTS" in flair text and 
// serializing the original post data into the metadata field.
func ProcessResponse(resp RedditResponse) []StorablePost {
  posts := make([]StorablePost, 0, len(resp.Data.Children))

  for _, child := range resp.Data.Children {
    data := child.Data

    // Determine if the post is "Active" based on WTS (Want To Sell) flair
    isActive := hasWTSFlair(data.LinkFlairRichText)

    // Mirroring the Rust logic: Serialize the post data into a map for the Metadata field
    var metadata map[string]interface{}
    rawBytes, err := json.Marshal(data)
    if err == nil {
      _ = json.Unmarshal(rawBytes, &metadata)
    }

    posts = append(posts, StorablePost{
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

// hasWTSFlair performs the case-insensitive "WTS" check within the flair rich text.
func hasWTSFlair(flairs []map[string]interface{}) bool {
  for _, flair := range flairs {
    // Check the "t" key for text content as seen in the Rust f.get("t") logic
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
