package pipeline

import (
  "context"
  "log"
  "os"
  "sync"

  "github.com/google/uuid"
  "github.com/jmoiron/sqlx"
  "github.com/openai/openai-go/v3"
  llmPkg "leaddits/internal/pkg/llm"
  pg "leaddits/internal/pkg/pg"
  "leaddits/internal/pipeline/filters"
)

type PipelineEngine struct {
  DB        *sqlx.DB
  LLMClient *llmPkg.Client
}

// NewPipelineEngine handles initialization of DB and LLM
func NewPipelineEngine() (*PipelineEngine, error) {
  db, err := pg.Connect(os.Getenv("DATABASE_URL"))
  if err != nil {
    return nil, err
  }

  llmClient := llmPkg.NewClient(os.Getenv("OPENAI_API_KEY"))

  return &PipelineEngine{
    DB:        db,
    LLMClient: llmClient,
  }, nil
}

// RunDataExtraction handles Merge -> Clean -> Extract -> Bulk Update
func (e *PipelineEngine) RunDataExtraction(ctx context.Context, limit int) error {
  posts, err := pg.FetchPostsToProcess(e.DB, "extraction", limit)
  if err != nil || len(posts) == 0 {
    log.Println("😴 No new posts needing extraction.")
    return err
  }

  log.Printf("🧐 Processing %d posts for extraction...", len(posts))

  priceUpdates := make(map[uuid.UUID]interface{})
  notesUpdates := make(map[uuid.UUID]interface{})

  var mu sync.Mutex
  var wg sync.WaitGroup
  semaphore := make(chan struct{}, 5)

  for _, post := range posts {
    wg.Add(1)
    go func(p pg.RedditPost) {
      defer wg.Done()
      semaphore <- struct{}{}
      defer func() { <-semaphore }()

      payload := &filters.ExtractionPayload{Post: p}

      content := ""
      if p.Content != nil {
        content = *p.Content
      }
      merged := filters.MergePostData(p.Title, content)
      payload.CleanedText = filters.CleanPostText(merged)

      if err := filters.ExtractProductDetails(ctx, e.LLMClient, payload); err != nil {
        log.Printf("[!] Extraction error for %s: %v", p.ID, err)
        return
      }

      mu.Lock()
      priceUpdates[p.ID] = payload.Extraction.Prices
      notesUpdates[p.ID] = payload.Extraction.Notes
      mu.Unlock()

      log.Printf("✅ Extracted: %s...", p.Title[:20])
    }(post)
  }

  wg.Wait()

  if len(priceUpdates) > 0 {
    if err := pg.BulkUpdatePostData(e.DB, "price", priceUpdates); err != nil {
      return err
    }
    if err := pg.BulkUpdatePostData(e.DB, "notes", notesUpdates); err != nil {
      return err
    }
    log.Printf("✨ Extraction complete: %d items updated.", len(priceUpdates))
  }

  return nil
}

// RunDataVectorization handles Category -> Assembly -> Vectorize -> Bulk Update
func (e *PipelineEngine) RunDataVectorization(ctx context.Context, limit int) error {
  posts, err := pg.FetchPostsToProcess(e.DB, "vectorization", limit)
  if err != nil || len(posts) == 0 {
    log.Println("😴 No posts ready for vectorization.")
    return err
  }

  log.Printf("🚀 Generating embeddings for %d posts...", len(posts))

  embeddingUpdates := make(map[uuid.UUID][]float32)
  var mu sync.Mutex
  var wg sync.WaitGroup
  semaphore := make(chan struct{}, 10)

  for _, post := range posts {
    wg.Add(1)
    go func(p pg.RedditPost) {
      defer wg.Done()
      semaphore <- struct{}{}
      defer func() { <-semaphore }()

      payload := &filters.VectorizationPayload{Post: p}      
      payload.Category = filters.ExtractCategory(p.Metadata)
      payload.AssembledText = filters.AssembleEmbeddingText(payload, payload.Category)

      if err := filters.GenerateEmbedding(ctx, e.LLMClient, payload, payload.AssembledText); err != nil {
        log.Printf("[!] Embedding error for %s: %v", p.ID, err)
        return
      }

      mu.Lock()
      embeddingUpdates[p.ID] = payload.Embedding
      mu.Unlock()
    }(post)
  }

  wg.Wait()

  if len(embeddingUpdates) > 0 {
    if err := pg.BulkUpdateEmbeddings(e.DB, embeddingUpdates); err != nil {
      return err
    }
    log.Printf("✨ Storage complete: %d vectors generated.", len(embeddingUpdates))
  }

  return nil
}

