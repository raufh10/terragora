package scraper

import (
  "context"
  "fmt"
  "time"

  "github.com/jmoiron/sqlx"
  _ "github.com/lib/pq" // Postgres driver
)

// NewClient initializes a new scraper client with a database connection.
func NewClient(dbURL string, targets Targets, config ScraperConfigs) (*Client, error) {
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

  return &Client{
    DatabaseURL: dbURL,
    Targets:     targets,
    Config:      config,
  }, nil
}

// GetDB helper returns a configured sqlx.DB instance.
// Note: In a production app, you might want to store the *sqlx.DB 
// directly on the Client struct instead of just the URL string.
func (c *Client) Connect() (*sqlx.DB, error) {
  return sqlx.Connect("postgres", c.DatabaseURL)
}

