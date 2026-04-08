package main

import (
  "fmt"
  "log"
  "math/rand"
  "os"
  "time"

  natsPkg "leaddits/internal/pkg/nats"
)

func main() {
  // 1. Setup Config
  natsAddr := os.Getenv("NATS_URL")
  if natsAddr == "" {
    natsAddr = "nats://127.0.0.1:4222"
  }

  // 2. Initialize Client
  client, err := natsPkg.NewClient(natsAddr)
  if err != nil {
    log.Fatalf("Failed to connect: %v", err)
  }
  defer client.Close()

  // 3. Random Delay Logic
  min, max := 5, 30
  rand.Seed(time.Now().UnixNano())
  randomSeconds := rand.Intn(max-min+1) + min
  delay := time.Duration(randomSeconds) * time.Second

  fmt.Printf("Alarm triggered. Sleeping for %v...\n", delay)
  time.Sleep(delay)

  // 4. Prepare Event
  event := natsPkg.ScraperEvent{
    Pages:     5,
    Limit:     100,
    Target:    "jualbeliindonesia",
    Timestamp: time.Now().Format(time.RFC3339),
  }

  // 5. Execute Publish
  if err := client.PublishScraperEvent("scraper.event", event); err != nil {
    log.Fatalf("Publish error: %v", err)
  }

  fmt.Println("Event published successfully. Task complete.")
}

