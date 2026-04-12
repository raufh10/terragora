package pkg

import (
  "context"
  "fmt"
  "time"

  "github.com/jmoiron/sqlx"
  _ "github.com/lib/pq" // Postgres driver
)

// Connect provides a validated database handle based on the provided connection string.
// It performs a ping to ensure the database is reachable before returning.
func Connect(dbURL string) (*sqlx.DB, error) {
  db, err := sqlx.Open("postgres", dbURL)
  if err != nil {
    return nil, fmt.Errorf("failed to open database: %w", err)
  }

  // Basic connection health check
  ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
  defer cancel()

  if err := db.PingContext(ctx); err != nil {
    return nil, fmt.Errorf("failed to ping database: %w", err)
  }

  return db, nil
}

