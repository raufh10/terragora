package llm

import (
  "encoding/json"
  "github.com/invopop/jsonschema"
)

// StructuredTask couples a prompt with its specific JSON schema.
type StructuredTask struct {
  Name         string
  SystemPrompt string
  Schema       map[string]any
}

// NewStructuredTask is your factory function to build these pairs.
func NewStructuredTask[T any](name string, prompt string) StructuredTask {
  return StructuredTask{
    Name:         name,
    SystemPrompt: prompt,
    Schema:       GenerateSchema[T](),
  }
}

// GenerateSchema remains your internal helper for reflection.
func GenerateSchema[T any]() map[string]any {
  reflector := jsonschema.Reflector{
    AllowAdditionalProperties: false,
    DoNotReference:            true,
  }
  var v T
  schema := reflector.Reflect(v)

  data, _ := json.Marshal(schema)
  var result map[string]any
  json.Unmarshal(data, &result)
  return result
}
