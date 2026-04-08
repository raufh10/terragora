package botserver

import (
  "bytes"
  "context"
  "encoding/json"
  "fmt"
  "net/http"
  "strings"
  "time"

  "golang.org/x/text/language"
  "golang.org/x/text/message"
)

// SendMessage sends a Markdown formatted message to Telegram
func SendMessage(chatID int64, text string) {
  url := fmt.Sprintf("https://api.telegram.org/bot%s/sendMessage", GlobalConfig.TelegramBotToken)
  payload, _ := json.Marshal(map[string]interface{}{
    "chat_id":    chatID,
    "text":       text,
    "parse_mode": "Markdown",
  })
  http.Post(url, "application/json", bytes.NewBuffer(payload))
}

// SendChatAction sends a status (like 'typing') to the user
func SendChatAction(chatID int64, action string) {
  url := fmt.Sprintf("https://api.telegram.org/bot%s/sendChatAction", GlobalConfig.TelegramBotToken)
  payload, _ := json.Marshal(map[string]interface{}{
    "chat_id": chatID,
    "action":  action,
  })
  http.Post(url, "application/json", bytes.NewBuffer(payload))
}

// TypingLoop continuously sends the typing status until the context is cancelled
func TypingLoop(ctx context.Context, chatID int64) {
  ticker := time.NewTicker(4 * time.Second)
  defer ticker.Stop()
  for {
    select {
    case <-ctx.Done():
      return
    case <-ticker.C:
      SendChatAction(chatID, "typing")
    }
  }
}

// SanitizeInput cleans up user queries
func SanitizeInput(input string) string {
  text := strings.TrimSpace(input)
  if len(text) > 1000 {
    text = text[:1000]
  }
  return strings.Join(strings.Fields(text), " ")
}

// formatRp handles Indonesian currency formatting (e.g., 1.000.000)
func formatRp(value float64) string {
  p := message.NewPrinter(language.Indonesian)
  return p.Sprintf("%d", int64(value))
}

// FormatPrice decodes the json.RawMessage from the DB and formats it for display
func FormatPrice(rawPrice json.RawMessage) string {
  if len(rawPrice) == 0 || string(rawPrice) == "null" {
    return "Rp -"
  }

  var priceData interface{}
  if err := json.Unmarshal(rawPrice, &priceData); err != nil {
    return "Rp -"
  }

  var priceList []map[string]interface{}
  switch v := priceData.(type) {
  case []interface{}:
    for _, item := range v {
      if m, ok := item.(map[string]interface{}); ok {
        priceList = append(priceList, m)
      }
    }
  case map[string]interface{}:
    priceList = append(priceList, v)
  case float64:
    priceList = append(priceList, map[string]interface{}{"start": v})
  default:
    return "Rp -"
  }

  if len(priceList) == 0 {
    return "Rp -"
  }

  var parts []string
  var totalMin, totalMax float64
  var hasMax bool

  for _, p := range priceList {
    start, _ := p["start"].(float64)
    maxP, hasMaxP := p["max"].(float64)

    totalMin += start
    if hasMaxP {
      totalMax += maxP
      hasMax = true
      parts = append(parts, fmt.Sprintf("%s–%s", formatRp(start), formatRp(maxP)))
    } else {
      totalMax += start
      parts = append(parts, formatRp(start))
    }
  }

  priceLine := "Rp " + strings.Join(parts, ", ")

  if len(priceList) > 1 {
    totalStr := formatRp(totalMin)
    if hasMax {
      totalStr = fmt.Sprintf("%s–%s", formatRp(totalMin), formatRp(totalMax))
    }
    priceLine += fmt.Sprintf(" (Total: Rp %s)", totalStr)
  }

  return priceLine
}
