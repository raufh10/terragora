package main

import (
  "context"
  "fmt"
  "log"
  "os"

  "github.com/joho/godotenv"
  "github.com/jackc/pgx/v5"
)

func main() {
  // Load .env file
  err := godotenv.Load()
  if err != nil {
    log.Println("No .env file found (continuing with system env)")
  }

  // Read DATABASE_URL from environment
  connStr := os.Getenv("DATABASE_URL")
  if connStr == "" {
    log.Fatal("DATABASE_URL is not set")
  }

  ctx := context.Background()

  conn, err := pgx.Connect(ctx, connStr)
  if err != nil {
    fmt.Fprintf(os.Stderr, "Unable to connect to database: %v\n", err)
    os.Exit(1)
  }
  defer conn.Close(ctx)

  // Listen on the channel
  _, err = conn.Exec(ctx, "LISTEN reddit_posts_inserted")
  if err != nil {
    log.Fatalf("Failed to listen: %v", err)
  }

  fmt.Println("Bridge active: Waiting for notifications on channel 'reddit_posts_inserted'...")

  for {
    notification, err := conn.WaitForNotification(ctx)
    if err != nil {
      log.Fatalf("Error waiting for notification: %v", err)
    }

    fmt.Printf("Received Notification: %s\n", notification.Payload)
  }
}
