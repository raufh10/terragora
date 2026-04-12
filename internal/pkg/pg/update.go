package pkg

import (
  "encoding/json"
  "fmt"

  "github.com/google/uuid"
  "github.com/jmoiron/sqlx"
)

// BulkUpdateEmbeddings updates multiple post embeddings in a single transaction.
func BulkUpdateEmbeddings(db *sqlx.DB, updates map[uuid.UUID][]float32) error {
  tx, err := db.Beginx()
  if err != nil {
    return fmt.Errorf("failed to start transaction: %w", err)
  }

  defer tx.Rollback()

  query := `UPDATE reddit_posts SET embedding = $1::vector WHERE id = $2`

  for id, embedding := range updates {
    embStr, err := json.Marshal(embedding)
    if err != nil {
      return fmt.Errorf("failed to marshal embedding for %s: %w", id, err)
    }

    _, err = tx.Exec(query, string(embStr), id)
    if err != nil {
      return fmt.Errorf("failed to update id %s: %w", id, err)
    }
  }

  if err := tx.Commit(); err != nil {
    return fmt.Errorf("failed to commit embedding updates: %w", err)
  }

  fmt.Printf("✅ Successfully updated %d embeddings.\n", len(updates))
  return nil
}

// BulkUpdatePostData updates a specific column for multiple posts.
func BulkUpdatePostData(db *sqlx.DB, columnName string, updates map[uuid.UUID]interface{}) error {
  tx, err := db.Beginx()
  if err != nil {
    return fmt.Errorf("failed to start transaction: %w", err)
  }

  defer tx.Rollback()

  query := fmt.Sprintf(`UPDATE reddit_posts SET %s = $1 WHERE id = $2`, columnName)

  for id, val := range updates {
    var finalVal interface{} = val
    if columnName == "price" || columnName == "metadata" {
      bytes, err := json.Marshal(val)
      if err != nil {
        return fmt.Errorf("failed to marshal json for %s: %w", id, err)
      }
      finalVal = string(bytes)
    }

    _, err = tx.Exec(query, finalVal, id)
    if err != nil {
      return fmt.Errorf("failed to update %s for id %s: %w", columnName, id, err)
    }
  }

  if err := tx.Commit(); err != nil {
    return fmt.Errorf("failed to commit %s updates: %w", columnName, err)
  }

  fmt.Printf("✅ Successfully updated %d records in '%s'.\n", len(updates), columnName)
  return nil
}
