package pipeline

import (
  "context"
  "fmt"
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

// LLMWrapper adapts the raw openai.Client to the interfaces defined in filters.
type LLMWrapper struct {
  api *openai.Client
}

func (w *LLMWrapper) ExecuteTask(ctx context.Context, input string, task llmPkg.StructuredTask) ([]byte, error) {
  fullInput := fmt.Sprintf("%s\n\nInput:\n%s", task.SystemPrompt, input)
  return llmPkg.CallOpenAIWithSchema(ctx, w.api, fullInput, task.Name, task.Schema)
}

func (w *LLMWrapper) CreateEmbedding(ctx context.Context, input string) ([]float32, error) {
  return llmPkg.GetEmbedding(ctx, w.api, input)
}

type PipelineEngine struct {
  DB        *sqlx.DB
  LLMClient *LLMWrapper
}

// NewPipelineEngine handles initialization of DB and LLM
func NewPipelineEngine() (*PipelineEngine, error) {
  db, err := pg.Connect(os.Getenv("DATABASE_URL"))
  if err != nil {
    return nil, err
  }

  rawClient := llmPkg.NewClient(os.Getenv("OPENAI_API_KEY"))

  return &PipelineEngine{
    DB:        db,
    LLMClient: &LLMWrapper{api: rawClient},
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
  allUpdates := make(map[uuid.UUID]map[string]interface{})

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
      allUpdates[p.ID] = map[string]interface{}{
        "price": payload.Extraction.Prices,
        "notes": payload.Extraction.Notes,
      }
      mu.Unlock()

      log.Printf("✅ Extracted: %s...", p.Title)
    }(post)
  }

  wg.Wait()

  if len(allUpdates) > 0 {
    if err := pg.BulkUpdatePostData(e.DB, allUpdates); err != nil {
      return err
    }
    log.Printf("✨ Extraction complete: %d items updated in bulk.", len(allUpdates))
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
