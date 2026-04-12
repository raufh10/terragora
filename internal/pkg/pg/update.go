package pkg

import (
  "encoding/json"
  "fmt"
  "strings"

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

// BulkUpdatePostData handles multiple column updates for multiple posts in one transaction.
func BulkUpdatePostData(db *sqlx.DB, updates map[uuid.UUID]map[string]interface{}) error {
  if len(updates) == 0 {
    return nil
  }

  tx, err := db.Beginx()
  if err != nil {
    return fmt.Errorf("failed to start transaction: %w", err)
  }
  defer tx.Rollback()

  for id, cols := range updates {
    setClauses := []string{}
    args := []interface{}{}
    argCount := 1

    for colName, val := range cols {
      var finalVal interface{} = val
      
      if colName == "price" || colName == "metadata" || colName == "extraction" {
        bytes, err := json.Marshal(val)
        if err != nil {
          return fmt.Errorf("failed to marshal json for %s (id: %s): %w", colName, id, err)
        }
        finalVal = string(bytes)
      }

      setClauses = append(setClauses, fmt.Sprintf("%s = $%d", colName, argCount))
      args = append(args, finalVal)
      argCount++
    }

    args = append(args, id)
    query := fmt.Sprintf("UPDATE reddit_posts SET %s WHERE id = $%d", 
      strings.Join(setClauses, ", "), 
      argCount,
    )

    _, err = tx.Exec(query, args...)
    if err != nil {
      return fmt.Errorf("failed to update post %s: %w", id, err)
    }
  }

  if err := tx.Commit(); err != nil {
    return fmt.Errorf("failed to commit bulk updates: %w", err)
  }

  fmt.Printf("✅ Successfully updated %d records across multiple columns.\n", len(updates))
  return nil
}
