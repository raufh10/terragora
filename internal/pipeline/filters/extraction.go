package filters

import (
  "context"
  "encoding/json"
  "fmt"
  llmPkg "leaddits/internal/pkg/llm"
)

// 1. SCHEMAS
type PriceRange struct {
  Start *float64 `json:"start" jsonschema_description:"The fixed price or the lower bound of a range."`
  Max   *float64 `json:"max" jsonschema_description:"The upper bound of a price range if provided."`
}

type ProductExtraction struct {
  Prices []PriceRange `json:"prices" jsonschema_description:"List of prices or price ranges extracted."`
  Notes  string       `json:"notes" jsonschema_description:"1-3 sentences regarding condition, location, or bundle details."`
}

// 2. SYSTEM PROMPT
const productExtractionPrompt = `You are a specialist in secondary market pricing. 
Extract all mentioned prices from the post. 
If a range is given (e.g. 100-150), set start to 100 and max to 150. 
Provide a brief note about the item's condition.`

// 3. PIPELINE CLIENT
type LLMClient interface {
  ExecuteTask(ctx context.Context, input string, task llmPkg.StructuredTask) ([]byte, error)
}

// 4. THE FILTER LOGIC
func ExtractProductDetails(ctx context.Context, client LLMClient, payload *ExtractionPayload) error {
  if payload.CleanedText == "" {
    return fmt.Errorf("cannot extract details from empty text")
  }

  task := llmPkg.NewStructuredTask[ProductExtraction](
    "product_extraction",
    productExtractionPrompt,
  )

  rawBytes, err := client.ExecuteTask(ctx, payload.CleanedText, task)
  if err != nil {
    return fmt.Errorf("extraction failed: %w", err)
  }

  var extracted ProductExtraction
  if err := json.Unmarshal(rawBytes, &extracted); err != nil {
    return fmt.Errorf("failed to parse llm response into local struct: %w", err)
  }

  payload.Extraction = extracted
  return nil
}
