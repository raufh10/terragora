package filters

import (
  "encoding/json"
  "strings"
)

// ExtractCategory pulls the flair text from the Reddit metadata.
// Defaults to "General" if no text flair is found.
func ExtractCategory(metadata json.RawMessage) string {
  var meta map[string]interface{}
  if err := json.Unmarshal(metadata, &meta); err != nil {
    return "General"
  }

  richtext, ok := meta["link_flair_richtext"].([]interface{})
  if !ok || len(richtext) == 0 {
    return "General"
  }

  var categories []string
  for _, item := range richtext {
    if m, ok := item.(map[string]interface{}); ok {
      // We only want elements where type (e) is 'text'
      if m["e"] == "text" {
        if t, ok := m["t"].(string); ok {
          categories = append(categories, t)
        }
      }
    }
  }

  result := strings.Join(categories, " ")
  if strings.TrimSpace(result) == "" {
    return "General"
  }
  return strings.TrimSpace(result)
}

