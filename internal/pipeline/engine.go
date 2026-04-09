package pipeline

import (
  "context"
  "log"
  "sync"

  "github.com/google/uuid"
  "github.com/jmoiron/sqlx"
  llmPkg "leaddits/internal/pkg/llm"
  pg "leaddits/internal/pkg/pg"
  "leaddits/internal/pipeline/filters"
)

type PipelineEngine struct {
  DB        *sqlx.DB
  LLMClient Client // Refers to the local interface in clients.go
}

func NewPipelineEngine(db *sqlx.DB, llmClient Client) *PipelineEngine {
  return &PipelineEngine{DB: db, LLMClient: llmClient}
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

      // 1. Initialize Payload from filters package
      payload := &filters.ExtractionPayload{Post: p}

      // 2. Run Text Processing Filters
      content := ""
      if p.Content != nil {
        content = *p.Content
      }
      merged := filters.MergePostData(p.Title, content)
      payload.CleanedText = filters.CleanPostText(merged)

      // 3. Run LLM Extraction Filter
      if err := filters.ExtractProductDetails(ctx, e.LLMClient, payload); err != nil {
        log.Printf("[!] Extraction error for %s: %v", p.ID, err)
        return
      }

      // 4. Thread-safe collection of updates
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

// RunDataVectorization handles Category -> Price -> Assembly -> Vectorize -> Bulk Update
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

      // 1. Initialize Payload from filters package
      payload := &filters.VectorizationPayload{Post: p}

      // 2. Prepare context for assembly
      payload.Category = filters.ExtractCategory(p.Metadata)

      var prices []llmPkg.PriceRange
      if err := pg.UnmarshalJSONB(p.Price, &prices); err != nil {
        log.Printf("[!] Price unmarshal skipped for %s: %v", p.ID, err)
      }

      formattedPrice := filters.FormatPrice(prices)
      payload.AssembledText = filters.AssembleEmbeddingText(payload, payload.Category, formattedPrice)

      // 3. Generate Vector Embedding
      if err := filters.GenerateEmbedding(ctx, e.LLMClient, payload, payload.AssembledText); err != nil {
        log.Printf("[!] Embedding error for %s: %v", p.ID, err)
        return
      }

      // 4. Thread-safe collection
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

