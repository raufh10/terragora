package llm

import (
  "context"
  "fmt"
  "log"
  "time"

  "github.com/openai/openai-go/v3"
)

// GetEmbedding converts text to a 1536-dimensional vector.
func GetEmbedding(ctx context.Context, client *openai.Client, text string) ([]float32, error) {
  for i := 0; i < MaxRetries; i++ {
    res, err := client.Embeddings.New(ctx, openai.EmbeddingNewParams{
      Input: openai.EmbeddingNewParamsInputUnion{
        OfString: openai.String(text),
      },
      Model:      openai.EmbeddingModelTextEmbedding3Small,
      Dimensions: openai.Int(1536),
    })

    if err == nil {
      if len(res.Data) == 0 {
        return nil, fmt.Errorf("empty embedding data returned")
      }
      embeddings := make([]float32, len(res.Data[0].Embedding))
      for j, v := range res.Data[0].Embedding {
        embeddings[j] = float32(v)
      }
      return embeddings, nil
    }

    log.Printf("⚠️ Embedding failed (attempt %d): %v", i+1, err)
    time.Sleep(RetryDelay)
  }
  return nil, fmt.Errorf("failed after %d retries", MaxRetries)
}
