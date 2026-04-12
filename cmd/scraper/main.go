package main

import (
  "context"
  "log"
  "time"

  "leaddits/internal/pkg"
  "leaddits/internal/scraper"
)

func main() {
  client, err := scraper.NewConfig()
  if err != nil {
    log.Fatalf("[-] Failed to initialize config: %v", err)
  }

  db, err := pkg.Connect(client.DatabaseURL)
  if err != nil {
    log.Fatalf("[-] Database connection error: %v", err)
  }
  defer db.Close()
  log.Println("[+] Connected to database successfully")

  httpClient, err := client.InitHttpClient()
  if err != nil {
    log.Fatalf("[-] HTTP Client error: %v", err)
  }

  ctx := context.Background()

  for _, sub := range client.Targets.Subreddits {
    log.Printf("[*] Starting scrape for r/%s", sub)

    currentURL := client.GetSubredditURL(sub)
    pagesScraped := 0
    const maxPages = 2

    for currentURL != "" && pagesScraped < maxPages {
      log.Printf("[>] Fetching page %d: %s", pagesScraped+1, currentURL)

      var resp *scraper.RedditResponse
      var fetchErr error
      
      // --- Retry Logic Start ---
      for attempt := 1; attempt <= 3; attempt++ {
        ua := scraper.UserAgent{Raw: client.Config.LastUsedUA}
        resp, fetchErr = client.FetchSubredditJson(httpClient, currentURL, ua)
        
        if fetchErr == nil {
          break
        }

        log.Printf("[!] Attempt %d failed for r/%s: %v", attempt, sub, fetchErr)
        
        if attempt < 3 {
          backoff := getBackoffDuration(attempt)
          log.Printf("[*] Retrying in %v...", backoff)
          time.Sleep(backoff)
          
          // Rotate session on failure to try a new IP/UA
          _ = client.RotateSession() 
        }
      }

      if fetchErr != nil {
        log.Printf("[!!] Max retries reached for %s. Skipping page.", currentURL)
        break
      }
      // --- Retry Logic End ---

      posts := scraper.ProcessResponse(*resp)
      log.Printf("[+] Parsed %d posts from r/%s", len(posts), sub)

      if len(posts) > 0 {
        if err := pkg.BulkIngestRawPosts(ctx, db, posts); err != nil {
          log.Printf("[!] Database ingestion error: %v", err)
        } else {
          log.Printf("[+] Successfully upserted batch for r/%s", sub)
        }
      }

      if resp.Data.After != nil && *resp.Data.After != "" {
        currentURL = client.GetSubredditPaginationURL(sub, *resp.Data.After)
        pagesScraped++

        if err := client.RotateSession(); err != nil {
          log.Printf("[!] Session rotation failed: %v", err)
        }
        time.Sleep(2 * time.Second)
      } else {
        log.Printf("[*] Reached end of r/%s", sub)
        currentURL = "" 
      }
    }
  }

  log.Println("[+] Scraping cycle completed.")
}

// getBackoffDuration returns 10s, 20s, or 30s based on attempt number
func getBackoffDuration(attempt int) time.Duration {
  switch attempt {
  case 1:
    return 10 * time.Second
  case 2:
    return 20 * time.Second
  case 3:
    return 30 * time.Second
  default:
    return 10 * time.Second
  }
}

