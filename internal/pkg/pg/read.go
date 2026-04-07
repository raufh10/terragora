package pkg

import (
  "encoding/json"
  "fmt"

  "github.com/jmoiron/sqlx"
)

// FetchRelevantPosts executes a Cosine Similarity search using pgvector.
func FetchRelevantPosts(db *sqlx.DB, queryEmbedding []float32, limit int) ([]RedditPost, error) {
  query := `
    SELECT 
      id, reddit_id, title, content, price, metadata, is_active,
      1 - (embedding <=> $1::vector) AS similarity
    FROM reddit_posts
    WHERE is_active = true
    ORDER BY embedding <=> $1::vector
    LIMIT $2;
  `

  // Format the float slice into a string: "[0.1, 0.2, ...]"
  embeddingStr, err := formatEmbedding(queryEmbedding)
  if err != nil {
    return nil, fmt.Errorf("failed to encode embedding: %w", err)
  }

  var posts []RedditPost
  err = db.Select(&posts, query, embeddingStr, limit)
  if err != nil {
    return nil, fmt.Errorf("database query failed: %w", err)
  }

  return posts, nil
}

// formatEmbedding converts the Go slice to a format pgvector recognizes.
func formatEmbedding(v []float32) (string, error) {
  j, err := json.Marshal(v)
  if err != nil {
    return "", err
  }
  return string(j), nil
}
