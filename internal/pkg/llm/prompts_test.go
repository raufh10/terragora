package llm

import (
  "testing"
)

func TestGenerateSchema(t *testing.T) {
  t.Run("Valid Schema Generation", func(t *testing.T) {
    schema := GenerateSchema[MarketplaceSearch]()

    if schema == nil {
      t.Fatal("generated schema is nil")
    }

    properties, ok := schema["properties"].(map[string]any)
    if !ok {
      t.Error("schema missing properties field")
    }

    if _, ok := properties["listings"]; !ok {
      t.Error("schema missing 'listings' property")
    }
  })
}

