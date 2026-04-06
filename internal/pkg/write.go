package scraper

import (
  "context"
  "encoding/json"
  "time"

  "github.com/jmoiron/sqlx"
  "github.com/lib/pq"
)

// BulkIngestRawPosts performs a batch upsert into the reddit_posts table.
func BulkIngestRawPosts(ctx context.Context, db *sqlx.DB, posts []StorablePost) error {
  if len(posts) == 0 {
    return nil
  }

  redditIDs := make([]string, len(posts))
  titles := make([]string, len(posts))
  contents := make([]string, len(posts))
  urls := make([]string, len(posts))
  postedAts := make([]time.Time, len(posts))
  metadatas := make([][]byte, len(posts))
  isActives := make([]bool, len(posts))

  for i, p := range posts {
    redditIDs[i] = p.RedditID
    titles[i] = p.Title
    contents[i] = p.Content
    urls[i] = p.URL
    
    // Convert float64 timestamp to time.Time
    postedAts[i] = time.Unix(int64(p.PostedAt), 0).UTC()

    // Marshal metadata map back to JSON for Postgres jsonb
    metaJSON, err := json.Marshal(p.Metadata)
    if err != nil {
      metadatas[i] = []byte("{}")
    } else {
      metadatas[i] = metaJSON
    }

    isActives[i] = p.IsActive
  }

  const query = `
    INSERT INTO reddit_posts (reddit_id, title, content, url, posted_at, metadata, is_active)
    SELECT * FROM UNNEST(
      $1::text[], 
      $2::text[], 
      $3::text[], 
      $4::text[], 
      $5::timestamptz[], 
      $6::jsonb[],
      $7::boolean[]
    )
    ON CONFLICT (reddit_id) DO UPDATE SET
      title = EXCLUDED.title,
      content = EXCLUDED.content,
      metadata = EXCLUDED.metadata,
      is_active = EXCLUDED.is_active,
      scraped_at = NOW();
  `

  _, err := db.ExecContext(
    ctx, 
    query,
    pq.Array(redditIDs),
    pq.Array(titles),
    pq.Array(contents),
    pq.Array(urls),
    pq.Array(postedAts),
    pq.Array(metadatas),
    pq.Array(isActives),
  )

  return err
}

