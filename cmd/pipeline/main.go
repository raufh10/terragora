package main

import (
  "context"
  "fmt"
  "log"
  "os"
  "os/signal"
  "syscall"

  "github.com/joho/godotenv"
  natsPkg "leaddits/internal/pkg/nats"
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

  engine, err := pipeline.NewPipelineEngine()
  if err != nil {
    log.Printf("[!] Engine init failed: %v", err)
    return
  }
  defer engine.DB.Close()

  if err := engine.RunDataExtraction(ctx, 100); err != nil {
    log.Printf("[!] Extraction pipeline error: %v", err)
  }
}

func handleVectorization(ctx context.Context, batch []natsPkg.PipelineEvent) {
  log.Printf("[>] Vectorization triggered for batch of %d", len(batch))

  engine, err := pipeline.NewPipelineEngine()
  if err != nil {
    log.Printf("[!] Engine init failed: %v", err)
    return
  }
  defer engine.DB.Close()

  if err := engine.RunDataVectorization(ctx, 100); err != nil {
    log.Printf("[!] Vectorization pipeline error: %v", err)
  }
}

