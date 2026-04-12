package security

import (
  "fmt"
  "strings"
  "unicode"
)

func SanitizeInput(input string) (string, error) {
  text := strings.TrimSpace(input)

  if text == "" {
    return "", fmt.Errorf("input is empty")
  }

  // Reject Telegram commands (strings starting with /)
  if strings.HasPrefix(text, "/") {
    return "", fmt.Errorf("commands are not allowed: text only please")
  }

  // Text-only verification (must contain at least one letter or number)
  found := false
  for _, r := range text {
    if unicode.IsLetter(r) || unicode.IsNumber(r) {
      found = true
      break
    }
  }
  if !found {
    return "", fmt.Errorf("invalid input: text only please")
  }

  // Remove redundant whitespace
  text = strings.Join(strings.Fields(text), " ")

  // Enforce length limit
  const maxSearchLen = 200
  if len(text) > maxSearchLen {
    text = text[:maxSearchLen]
  }

  return text, nil
}

