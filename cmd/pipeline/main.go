package main

import (
  "context"
  "fmt"
  "log"
  "os"
  "os/signal"
  "syscall"

  "github.com/joho/godotenv"

  llmPkg "leaddits/internal/pkg/llm"
  natsPkg "leaddits/internal/pkg/nats"
  pgPkg "leaddits/internal/pkg/pg"

  "leaddits/internal/pipeline"
)

func main() {
  _ = godotenv.Load()

  natsURL := os.Getenv("NATS_URL")
  if natsURL == "" {
    natsURL = "nats://127.0.0.1:4222"
  }

  // Primary NATS connection for the listener
  natsClient, err := natsPkg.NewClient(natsURL)
  if err != nil {
    log.Fatalf("[-] NATS connection failed: %v", err)
  }
  defer natsClient.Close()

  ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
  defer stop()

  fmt.Println("[+] Pipeline worker online. Listening for events...")

  // 1. Subscribe to INSERTS -> Extraction
  err = natsClient.SubscribeToPipeline("reddit_posts_inserted", func(batch []natsPkg.PipelineEvent) {
    handleExtraction(ctx, batch)
  })

  // 2. Subscribe to UPDATES -> Vectorization
  err = natsClient.SubscribeToPipeline("reddit_posts_updated", func(batch []natsPkg.PipelineEvent) {
    handleVectorization(ctx, batch)
  })

  if err != nil {
    log.Fatalf("[-] Subscription failed: %v", err)
  }

  <-ctx.Done()
  fmt.Println("[!] Pipeline worker shutting down...")
}

// handleExtraction handles logic for newly inserted posts
func handleExtraction(ctx context.Context, batch []natsPkg.PipelineEvent) {
  log.Printf("[>] Extraction triggered for batch of %d", len(batch))
  
  db, llmClient, err := initDeps()
  if err != nil {
    log.Printf("[!] Dep init failed: %v", err)
    return
  }
  defer db.Close()

  engine := pipeline.NewPipelineEngine(db, llmClient)
  if err := engine.RunDataExtraction(ctx, 100); err != nil {
    log.Printf("[!] Extraction pipeline error: %v", err)
  }
}

// handleVectorization handles logic for updated posts (extracted but not vectorized)
func handleVectorization(ctx context.Context, batch []natsPkg.PipelineEvent) {
  log.Printf("[>] Vectorization triggered for batch of %d", len(batch))

  db, llmClient, err := initDeps()
  if err != nil {
    log.Printf("[!] Dep init failed: %v", err)
    return
  }
  defer db.Close()

  engine := pipeline.NewPipelineEngine(db, llmClient)
  if err := engine.RunDataVectorization(ctx, 100); err != nil {
    log.Printf("[!] Vectorization pipeline error: %v", err)
  }
}

// initDeps creates fresh connections for the specific handler run
func initDeps() (*pgPkg.DB, llmPkg.Client, error) {
  db, err := pgPkg.Connect(os.Getenv("DATABASE_URL"))
  if err != nil {
    return nil, nil, err
  }

  llmClient := llmPkg.NewClient(os.Getenv("OPENAI_API_KEY"))
  return db, llmClient, nil
}

