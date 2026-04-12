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

// Global state for pooling
var (
  pool      []natsPkg.PipelineEvent
  poolMutex sync.Mutex
  lastAdded time.Time
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

  // 3. Start DB Listener
  err = pgPkg.ListenForEvents(dbURL, "reddit_posts_channel", func(payload string) {
    collectPipelineEvent(payload)
  })
  if err != nil {
    log.Fatalf("[-] DB Listener error: %v", err)
  }

  select {}
}

func collectPipelineEvent(payload string) {
  var dbRow natsPkg.PipelineEvent
  if err := json.Unmarshal([]byte(payload), &dbRow); err != nil {
    log.Printf("[!] Failed to decode DB payload: %v", err)
    return
  }

  poolMutex.Lock()
  pool = append(pool, dbRow)
  lastAdded = time.Now()
  count := len(pool)
  poolMutex.Unlock()

  log.Printf("[*] Pooled event %s (Current batch size: %d)", dbRow.RedditID, count)
}

func startFlusher(client *natsPkg.Client) {
  ticker := time.NewTicker(1 * time.Minute)
  for range ticker.C {
    poolMutex.Lock()
    
    // Check if pool has data AND if it's been 5 mins since last activity
    shouldFlush := len(pool) > 0 && time.Since(lastAdded) >= 5*time.Minute
    
    // Optional: Auto-flush if batch is very large (e.g., > 500 items) regardless of time
    if len(pool) >= 500 {
      shouldFlush = true
    }

    if shouldFlush {
      batchToSend := pool
      pool = nil
      poolMutex.Unlock()

      log.Printf("[^] Flushing %d events to NATS after idle period...", len(batchToSend))
      if err := client.PublishPipelineBatch("pipeline.event", batchToSend); err != nil {
        log.Printf("[!] Batch Publish error: %v", err)
      }
    } else {
      poolMutex.Unlock()
    }
  }
}

func publishScraperTrigger(client *natsPkg.Client) {
  min, max := 5, 30
  rand.Seed(time.Now().UnixNano())
  randomSeconds := rand.Intn(max-min+1) + min
  delay := time.Duration(randomSeconds) * time.Second

  log.Printf("[*] Cron triggered. Delaying %v...", delay)
  time.Sleep(delay)

  event := natsPkg.ScraperEvent{
    Pages:     5,
    Limit:     100,
    Target:    "jualbeliindonesia",
    Timestamp: time.Now().Format(time.RFC3339),
  }

  if err := client.PublishScraperEvent("scraper.event", event); err != nil {
    log.Printf("[!] Scraper Publish error: %v", err)
  } else {
    log.Printf("[+] Published scraper.event for r/%s", event.Target)
  }
}

