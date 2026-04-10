package pkg

import "encoding/json"

// UnmarshalJSONB is a helper to convert json.RawMessage into a struct
func UnmarshalJSONB(data []byte, v interface{}) error {
  if len(data) == 0 || string(data) == "null" {
    return nil
  }
  return json.Unmarshal(data, v)
}

// formatEmbedding converts the Go slice to a format pgvector recognizes.
func formatEmbedding(v []float32) (string, error) {
  j, err := json.Marshal(v)
  if err != nil {
    return "", err
  }
  return string(j), nil
}
