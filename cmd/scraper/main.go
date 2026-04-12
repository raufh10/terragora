package main

import (
  "context"
  "log"
  "time"

  "scraper/internal/pkg/scraper" // Adjust this path based on your go.mod
)

func main() {
  // 1. Initialize Configuration and Client
  client, err := scraper.NewConfig()
  if err != nil {
    log.Fatalf("Configuration error: %v", err)
  }

  // 2. Connect to Database
  db, err := client.Connect()
  if err != nil {
    log.Fatalf("Database connection error: %v", err)
  }
  defer db.Close()

  // 3. Initialize HTTP Client with Proxy and UA settings
  httpClient, err := client.InitHttpClient()
  if err != nil {
    log.Fatalf("HTTP Client error: %v", err)
  }

  ctx := context.Background()

  // 4. Iterate through targeted subreddits
  for _, sub := range client.Targets.Subreddits {
    log.Printf("Starting scrape for r/%s", sub)
    
    currentURL := client.GetSubredditURL(sub)
    pagesScraped := 0
    maxPages := 5 // Safety limit for the loop

    for currentURL != "" && pagesScraped < maxPages {
      log.Printf("Fetching: %s", currentURL)

      // Fetch Raw JSON from Reddit
      ua := scraper.UserAgent{Raw: client.Config.LastUsedUA}
      resp, err := client.FetchSubredditJson(httpClient, currentURL, ua)
      if err != nil {
        log.Printf("Error fetching r/%s: %v", sub, err)
        break
      }

      // Parse Reddit response into StorablePost format
      posts := scraper.ProcessResponse(*resp)
      log.Printf("Found %d posts (processing logic applied)", len(posts))

      // Bulk Ingest into Postgres
      if err := scraper.BulkIngestRawPosts(ctx, db, posts); err != nil {
        log.Printf("Database ingestion error: %v", err)
      } else {
        log.Printf("Successfully ingested batch from r/%s", sub)
      }

      // Handle Pagination
      if resp.Data.After != nil && *resp.Data.After != "" {
        currentURL = client.GetSubredditPaginationURL(sub, *resp.Data.After)
        pagesScraped++
        
        // Rotate session (Proxy/UA) every page to avoid rate limits
        if err := client.RotateSession(); err != nil {
          log.Printf("Session rotation failed: %v", err)
        }
        
        // Politeness delay
        time.Sleep(2 * time.Second)
      } else {
        currentURL = "" // End of the subreddit
      }
    }
  }

  log.Println("Scraping cycle completed.")
}

