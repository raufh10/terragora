package main

import (
  "encoding/json"
  "fmt"
  "log"
  "math/rand"
  "os"
  "sync"
  "time"

  "github.com/joho/godotenv"
  "github.com/robfig/cron/v3"
  natsPkg "leaddits/internal/pkg/nats"
  pgPkg "leaddits/internal/pkg/pg"
)

var (
  insertPool []natsPkg.PipelineEvent
  updatePool []natsPkg.PipelineEvent
  poolMutex  sync.Mutex
  lastAdded  = time.Now()
)

func main() {
  _ = godotenv.Load()

  natsAddr := os.Getenv("NATS_URL")
  if natsAddr == "" {
    natsAddr = "nats://127.0.0.1:4222"
  }
  dbURL := os.Getenv("DATABASE_URL")

  client, err := natsPkg.NewClient(natsAddr)
  if err != nil {
    log.Fatalf("[-] NATS connection error: %v", err)
  }
  defer client.Close()

  fmt.Printf("[+] Publisher service online. NATS: %s\n", natsAddr)

  // 1. Scraper Cron
  c := cron.New()
  schedule := os.Getenv("PUBLISH_SCHEDULE")
  if schedule == "" {
    schedule = "0 9 * * *"
  }
  c.AddFunc(schedule, func() { publishScraperTrigger(client) })
  c.Start()

  // 2. Start the Background Flusher
  go startFlusher(client)

  // 3. Listen for INSERTS (Starts the Extraction Pipeline)
  err = pgPkg.ListenForEvents(dbURL, "reddit_posts_inserted", func(payload string) {
    collectEvent("INSERT", payload)
  })
  if err != nil {
    log.Printf("[-] DB Insert Listener error: %v", err)
  }

  // 4. Listen for UPDATES (Starts the Vectorization Pipeline)
  err = pgPkg.ListenForEvents(dbURL, "reddit_posts_updated", func(payload string) {
    collectEvent("UPDATE", payload)
  })
  if err != nil {
    log.Printf("[-] DB Update Listener error: %v", err)
  }

  // Keep the process alive
  select {}
}

func collectEvent(opType string, payload string) {
  var event natsPkg.PipelineEvent
  if err := json.Unmarshal([]byte(payload), &event); err != nil {
    log.Printf("[!] Failed to decode DB payload: %v", err)
    return
  }

  poolMutex.Lock()
  defer poolMutex.Unlock()

  if opType == "INSERT" {
    insertPool = append(insertPool, event)
  } else {
    updatePool = append(updatePool, event)
  }

  lastAdded = time.Now()
  log.Printf("[*] Pooled %s: %s", opType, event.RedditID)
}

func startFlusher(client *natsPkg.Client) {
  ticker := time.NewTicker(1 * time.Minute)
  for range ticker.C {
    poolMutex.Lock()

    timeThreshold := time.Since(lastAdded) >= 5*time.Minute

    // Flush Insert Pool (Extraction Stage)
    if len(insertPool) >= 500 || (len(insertPool) > 0 && timeThreshold) {
      batch := insertPool
      insertPool = nil
      go client.PublishPipelineBatch("reddit_posts_inserted", batch)
      log.Printf("[^] Flushed %d INSERTS to Extraction Stage", len(batch))
    }

    // Flush Update Pool (Vectorization Stage)
    if len(updatePool) >= 500 || (len(updatePool) > 0 && timeThreshold) {
      batch := updatePool
      updatePool = nil
      go client.PublishPipelineBatch("reddit_posts_updated", batch)
      log.Printf("[^] Flushed %d UPDATES to Vectorization Stage", len(batch))
    }

    poolMutex.Unlock()
  }
}

func publishScraperTrigger(client *natsPkg.Client) {
  event := natsPkg.ScraperEvent{
    Pages:     5,
    Limit:     100,
    Target:    "jualbeliindonesia",
    Timestamp: time.Now().Format(time.RFC3339),
  }

  if err := client.PublishScraperEvent("scraper.event", event); err != nil {
    log.Printf("[!] Scraper Publish error: %v", err)
  }
}

