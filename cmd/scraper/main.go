package main

import (
  "context"
  "encoding/json"
  "log"
  "os"
  "time"

  "github.com/nats-io/nats.go"
  "github.com/joho/godotenv"
  
  natsPkg "leaddits/internal/pkg/nats" 
  pg "leaddits/internal/pkg/pg"
  "leaddits/internal/scraper"
)

func main() {
  _ = godotenv.Load()

  // 1. Initialize NATS Client Only
  natsURL := os.Getenv("NATS_URL")
  if natsURL == "" {
    natsURL = "nats://127.0.0.1:4222"
  }
  
  nc, err := natsPkg.NewClient(natsURL)
  if err != nil {
    log.Fatalf("[-] NATS connection error: %v", err)
  }
  defer nc.Close()

  // 2. Define the NATS Handler
  handleEvent := func(m *nats.Msg) {
    var event natsPkg.ScraperEvent
    if err := json.Unmarshal(m.Data, &event); err != nil {
      log.Printf("[!] JSON Unmarshal error: %v", err)
      return
    }

    log.Printf("[*] Event received for r/%s. Initializing job...", event.Target)
    
    // Trigger the self-contained scrape function
    scrape(event)
  }

  // 3. Start Listening
  _, err = nc.Listen("scraper.event", handleEvent)
  if err != nil {
    log.Fatalf("[-] Failed to subscribe: %v", err)
  }

  log.Println("[+] Scraper worker active. Waiting for NATS events...")
  
  // Keep process alive
  select {}
}

// scrape func (need adjustments for to be concurrent friendly)
func scrape(event natsPkg.ScraperEvent) {
  ctx := context.Background()

  // 1. Setup Scraper Config
  config, err := scraper.NewConfig()
  if err != nil {
    log.Printf("[-] Scraper config error: %v", err)
    return
  }

  // 2. Setup Database Connection
  dbURL := os.Getenv("DATABASE_URL")
  db, err := pg.Connect(dbURL)
  if err != nil {
    log.Printf("[-] Database connection error: %v", err)
    return
  }
  defer db.Close()

  httpClient, _ := config.InitHttpClient()

  // 3. Execution Logic
  sub := event.Target
  currentURL := config.GetSubredditURL(sub, event.Limit)
  pagesScraped := 0

  for currentURL != "" && pagesScraped < event.Pages {
    log.Printf("[>] [%s] Fetching page %d...", sub, pagesScraped+1)

    var resp *scraper.RedditResponse
    var fetchErr error

    for attempt := 1; attempt <= 3; attempt++ {
      ua := scraper.UserAgent{Raw: config.Config.LastUsedUA}
      resp, fetchErr = config.FetchSubredditJson(httpClient, currentURL, ua)

      if fetchErr == nil {
        break
      }

      if attempt < 3 {
        time.Sleep(scraper.GetBackoffDuration(attempt))
        _ = config.RotateSession()
      }
    }

    if fetchErr != nil {
      log.Printf("[!!] Terminating job for r/%s due to fetch errors", sub)
      break
    }

    posts := scraper.ProcessResponse(*resp)
    if len(posts) > 0 {
      if err := pg.BulkIngestRawPosts(ctx, db, posts); err != nil {
        log.Printf("[!] Ingestion error: %v", err)
      }
    }

    if resp.Data.After != nil && *resp.Data.After != "" {
      currentURL = config.GetSubredditPaginationURL(sub, *resp.Data.After, event.Limit)
      pagesScraped++
      _ = config.RotateSession()
      time.Sleep(2 * time.Second)
    } else {
      currentURL = ""
    }
  }

  log.Printf("[+] Job Finished: r/%s. Resources released.", sub)
}
