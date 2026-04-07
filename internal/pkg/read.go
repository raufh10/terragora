package pkg

import (
  "encoding/json"
  "fmt"

  "github.com/jmoiron/sqlx"
)

// RedditPost matches your DB schema for scanning
type RedditPost struct {
  ID         string          `db:"id"`
  Title      string          `db:"title"`
  Content    *string         `db:"content"` // Use pointer for nullable fields
  Price      json.RawMessage `db:"price"`   // jsonb maps well to RawMessage
  Metadata   json.RawMessage `db:"metadata"`
  Similarity float64         `db:"similarity"`
}

// FetchRelevantPosts replicates your Python logic using sqlx
func FetchRelevantPosts(db *sqlx.DB, queryEmbedding []float32, limit int) ([]RedditPost, error) {
  query := `
    SELECT 
      id, 
      title, 
      content, 
      price,
      metadata,
      1 - (embedding <=> $1::vector) AS similarity
    FROM reddit_posts
    WHERE is_active = true
    ORDER BY embedding <=> $1::vector
    LIMIT $2;
  `

  // Convert []float32 to the string format pgvector expects: "[0.1,0.2,0.3...]"
  embeddingStr := formatEmbedding(queryEmbedding)

  var posts []RedditPost
  err := db.Select(&posts, query, embeddingStr, limit)
  if err != nil {
    return nil, fmt.Errorf("error fetching posts: %w", err)
  }

  return posts, nil
}

// Helper to format slice for pgvector
func formatEmbedding(v []float32) string {
  j, _ := json.Marshal(v)
  return string(j)
}

