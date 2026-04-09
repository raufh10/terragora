package pkg

import "encoding/json"

// UnmarshalJSONB is a helper to convert json.RawMessage into a struct
func UnmarshalJSONB(data []byte, v interface{}) error {
  if len(data) == 0 || string(data) == "null" {
    return nil
  }
  return json.Unmarshal(data, v)
}
