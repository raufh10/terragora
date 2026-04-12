package filters

import (
  "fmt"
  "leaddits/internal/pkg/llm"
  "strings"

  "golang.org/x/text/language"
  "golang.org/x/text/message"
)

// FormatPrice turns PriceRange objects into a human-readable IDR string (Rp 1.000.000).
func FormatPrice(prices []llm.PriceRange) string {
  if len(prices) == 0 {
    return "Rp -"
  }

  p := message.NewPrinter(language.Indonesian)
  var parts []string
  var totalMin, totalMax float64
  var hasMax bool

  for _, pr := range prices {
    if pr.Start == nil && pr.Max == nil {
      continue
    }

    startVal := 0.0
    if pr.Start != nil {
      startVal = *pr.Start
      totalMin += startVal
    }

    if pr.Max != nil {
      totalMax += *pr.Max
      hasMax = true
      if pr.Start != nil {
        parts = append(parts, p.Sprintf("%.0f–%.0f", *pr.Start, *pr.Max))
      } else {
        parts = append(parts, p.Sprintf("%.0f", *pr.Max))
      }
    } else if pr.Start != nil {
      totalMax += startVal
      parts = append(parts, p.Sprintf("%.0f", *pr.Start))
    }
  }

  if len(parts) == 0 {
    return "Rp -"
  }

  // Replace commas with dots (Go's IDR printer uses dots, but ensure formatting)
  priceLine := "Rp " + strings.ReplaceAll(strings.Join(parts, ", "), ",", ".")

  if len(prices) > 1 {
    var totalStr string
    if hasMax {
      totalStr = p.Sprintf("%.0f–%.0f", totalMin, totalMax)
    } else {
      totalStr = p.Sprintf("%.0f", totalMin)
    }
    priceLine += fmt.Sprintf(" (Total: Rp %s)", strings.ReplaceAll(totalStr, ",", "."))
  }

  return priceLine
}

