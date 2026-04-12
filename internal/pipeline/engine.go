package pipeline

import (
  "context"
  "log"
  "sync"

  "github.com/google/uuid"
  "github.com/jmoiron/sqlx"
  "leaddits/internal/pkg/llm"
  "leaddits/internal/pkg/pg"
  "leaddits/internal/pipeline/filters"
)

type PipelineEngine struct {
  DB        *sqlx.DB
  LLMClient llm.Client
}

func NewPipelineEngine(db *sqlx.DB, llmClient llm.Client) *PipelineEngine {
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
  semaphore := make(chan struct{}, 5) // Limit to 5 concurrent LLM calls

  for _, post := range posts {
    wg.Add(1)
    go func(p pg.RedditPost) {
      defer wg.Done()
      semaphore <- struct{}{}
      defer func() { <-semaphore }()

      // 1. Initialize Payload
      payload := &ExtractionPayload{Post: p}

      // 2. Run Filters
      content := ""
      if p.Content != nil {
        content = *p.Content
      }
      merged := filters.MergePostData(p.Title, content)
      payload.CleanedText = filters.CleanPostText(merged)

      err := filters.ExtractProductDetails(ctx, e.LLMClient, payload)
      if err != nil {
        log.Printf("[!] Extraction error for %s: %v", p.ID, err)
        return
      }

      // 3. Prepare for Bulk Update (Thread-safe)
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
  semaphore := make(chan struct{}, 10) // Limit to 10 concurrent embedding calls

  for _, post := range posts {
    wg.Add(1)
    go func(p pg.RedditPost) {
      defer wg.Done()
      semaphore <- struct{}{}
      defer func() { <-semaphore }()

      // 1. Initialize Payload
      payload := &VectorizationPayload{Post: p}

      // 2. Run Filters
      payload.Category = filters.ExtractCategory(p.Metadata)
      
      // Need to unmarshal p.Price for Formatter (simplified for example)
      var prices []llm.PriceRange
      _ = pg.UnmarshalJSONB(p.Price, &prices) 
      
      formattedPrice := filters.FormatPrice(prices)
      payload.AssembledText = filters.AssembleEmbeddingText(payload, payload.Category, formattedPrice)

      // 3. Generate Vector
      err := filters.GenerateEmbedding(ctx, e.LLMClient, payload, payload.AssembledText)
      if err != nil {
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
    err := pg.BulkUpdateEmbeddings(e.DB, embeddingUpdates)
    if err != nil {
      return err
    }
    log.Printf("✨ Storage complete: %d vectors generated.", len(embeddingUpdates))
  }

  return nil
}

