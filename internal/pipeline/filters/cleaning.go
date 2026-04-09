package filters

import (
  "regexp"
  "strings"
)

var (
  urlRegex = regexp.MustCompile(`http\S+`)
  bracketRegex = regexp.MustCompile(`\[.*?\]`)
)

func CleanPostText(text string) string {
  if text == "" {
    return ""
  }

  text = urlRegex.ReplaceAllString(text, "")
  text = bracketRegex.ReplaceAllString(text, "")

  words := strings.Fields(text)
  return strings.Join(words, " ")
}

