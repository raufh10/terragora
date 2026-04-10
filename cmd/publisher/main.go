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
  lastAdded = time.Now()
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

  // 3. Listen for INSERTS
  go func() {
    err = pgPkg.ListenForEvents(dbURL, "reddit_posts_inserted", func(payload string) {
      collectPipelineEvent("INSERT", payload)
    })
    if err != nil {
      log.Printf("[-] DB Insert Listener error: %v", err)
    }
  }()

  // 4. Listen for UPDATES
  go func() {
    err = pgPkg.ListenForEvents(dbURL, "reddit_posts_updated", func(payload string) {
      collectPipelineEvent("UPDATE", payload)
    })
    if err != nil {
      log.Printf("[-] DB Update Listener error: %v", err)
    }
  }()

  // Keep the process alive
  select {}
}

func collectPipelineEvent(opType string, payload string) {
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

  log.Printf("[*] %s: Pooled event %s (Batch: %d)", opType, dbRow.RedditID, count)
}

func startFlusher(client *natsPkg.Client) {
  ticker := time.NewTicker(1 * time.Minute)
  for range ticker.C {
    poolMutex.Lock()

    shouldFlush := len(pool) > 0 && time.Since(lastAdded) >= 5*time.Minute
    if len(pool) >= 500 {
      shouldFlush = true
    }

    if shouldFlush {
      batchToSend := pool
      pool = nil
      poolMutex.Unlock()

      log.Printf("[^] Flushing %d combined events to NATS...", len(batchToSend))
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

