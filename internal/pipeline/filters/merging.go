package filters

import (
  "fmt"
  "strings"
)

func MergePostData(title string, content string) string {
  t := strings.TrimSpace(title)
  c := strings.TrimSpace(content)

  if t == "" {
    return c
  }
  if c == "" {
    return t
  }

  return fmt.Sprintf("%s\n%s", t, c)
}
