package main

import (
  "context"
  "fmt"
  "log"
  "os"
  "os/signal"
  "syscall"

  "github.com/joho/godotenv"
  "github.com/jmoiron/sqlx"
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

// initDeps uses the local pipeline.Client bridge to satisfy the engine
func initDeps() (*sqlx.DB, pipeline.Client, error) {
  db, err := pgPkg.Connect(os.Getenv("DATABASE_URL"))
  if err != nil {
    return nil, nil, err
  }

  // llmPkg.NewClient returns the raw client from your existing package
  rawLLM := llmPkg.NewClient(os.Getenv("OPENAI_API_KEY"))
  
  // Wrap it using the bridge in internal/pipeline/clients.go
  return db, pipeline.NewClientBridge(rawLLM), nil
}

