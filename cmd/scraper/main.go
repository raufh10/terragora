package main

import (
  "context"
  "log"
  "time"

  "leaddits/internal/pkg"
  "leaddits/internal/scraper"
)

func main() {
  // 1. Initialize Configuration
  // This calls scraper.NewConfig which loads .env and fetches User Agents
  client, err := scraper.NewConfig()
  if err != nil {
    log.Fatalf("[-] Failed to initialize config: %v", err)
  }

  // 2. Connect to Database 
  // Using the helper from internal/pkg
  db, err := pkg.Connect(client.DatabaseURL)
  if err != nil {
    log.Fatalf("[-] Database connection error: %v", err)
  }
  defer db.Close()
  log.Println("[+] Connected to database successfully")

  // 3. Initialize HTTP Client
  httpClient, err := client.InitHttpClient()
  if err != nil {
    log.Fatalf("[-] HTTP Client error: %v", err)
  }

  ctx := context.Background()

  // 4. Main Scrape Loop
  for _, sub := range client.Targets.Subreddits {
    log.Printf("[*] Starting scrape for r/%s", sub)
    
    currentURL := client.GetSubredditURL(sub)
    pagesScraped := 0
    const maxPages = 5 

    for currentURL != "" && pagesScraped < maxPages {
      log.Printf("[>] Fetching page %d: %s", pagesScraped+1, currentURL)

      // Fetch Raw JSON
      // We pass the last used UA from the client config
      ua := scraper.UserAgent{Raw: client.Config.LastUsedUA}
      resp, err := client.FetchSubredditJson(httpClient, currentURL, ua)
      if err != nil {
        log.Printf("[!] Error fetching r/%s: %v", sub, err)
        break
      }

      // 5. Parse Response
      // Uses internal/scraper/parser.go logic
      posts := scraper.ProcessResponse(*resp)
      log.Printf("[+] Parsed %d posts from r/%s", len(posts), sub)

      // 6. Bulk Ingest
      // Uses internal/pkg/write.go logic
      if len(posts) > 0 {
        if err := pkg.BulkIngestRawPosts(ctx, db, posts); err != nil {
          log.Printf("[!] Database ingestion error: %v", err)
        } else {
          log.Printf("[+] Successfully upserted batch for r/%s", sub)
        }
      }

      // 7. Pagination & Session Rotation
      if resp.Data.After != nil && *resp.Data.After != "" {
        currentURL = client.GetSubredditPaginationURL(sub, *resp.Data.After)
        pagesScraped++
        
        // Rotate Proxy Session and User Agent for the next page
        if err := client.RotateSession(); err != nil {
          log.Printf("[!] Session rotation failed: %v", err)
        }
        
        // Politeness delay to avoid 429s
        time.Sleep(2 * time.Second)
      } else {
        log.Printf("[*] Reached end of r/%s", sub)
        currentURL = "" 
      }
    }
  }

  log.Println("[+] Scraping cycle completed.")
}

