package pkg

import (
  "fmt"

  "github.com/jmoiron/sqlx"
)

// FetchRelevantPosts executes a Cosine Similarity search using pgvector.
func FetchRelevantPosts(db *sqlx.DB, queryEmbedding []float32, limit int) ([]RedditPost, error) {
  query := `
    SELECT 
      id, reddit_id, title, price, posted_at, notes
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

// FetchPostsToProcess retrieves a batch of posts that need either data extraction or vectorization.
func FetchPostsToProcess(db *sqlx.DB, batchType string, limit int) ([]RedditPost, error) {
  var query string

  switch batchType {
  case "extraction":
    query = `
      SELECT id, title, content, metadata 
      FROM reddit_posts 
      WHERE is_active = true 
      AND (notes IS NULL OR price IS NULL OR price = '[]'::jsonb)
      LIMIT $1`

  case "vectorization":
    query = `
      SELECT id, title, price, notes, metadata 
      FROM reddit_posts 
      WHERE is_active = true 
      AND notes IS NOT NULL 
      AND embedding IS NULL
      LIMIT $1`

  default:
    return nil, fmt.Errorf("unknown batch_type: %s", batchType)
  }

  var posts []RedditPost
  err := db.Select(&posts, query, limit)
  if err != nil {
    return nil, fmt.Errorf("failed to fetch posts for %s: %w", batchType, err)
  }

  return posts, nil
}
