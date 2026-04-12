package security

import (
  "fmt"
  "strings"
  "unicode"
)

func SanitizeInput(input string) (string, error) {
  if input == "" {
    return "", fmt.Errorf("input is empty")
  }

  // Text-only verification
  found := false
  for _, r := range input {
    if unicode.IsLetter(r) || unicode.IsNumber(r) {
      found = true
      break
    }
  }
  if !found {
    return "", fmt.Errorf("invalid input: text only please")
  }

  text := strings.TrimSpace(input)
  text = strings.Join(strings.Fields(text), " ")

  const maxSearchLen = 200
  if len(text) > maxSearchLen {
    text = text[:maxSearchLen]
  }

  return text, nil
}

