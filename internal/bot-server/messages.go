package botserver

import (
  "fmt"
  "sort"
  "strings"

  // Import the internal pkg where RedditPost is defined
  "leaddits/internal/pkg" 
  "golang.org/x/text/language"
  "golang.org/x/text/message"
)

// formatRp handles the Indonesian currency formatting (e.g., 1.000.000)
func formatRp(value float64) string {
  p := message.NewPrinter(language.Indonesian)
  return p.Sprintf("%d", int64(value))
}

// FormatPrice remains the same
func FormatPrice(price interface{}) string {
  if price == nil {
    return "Rp -"
  }

  var priceList []map[string]interface{}
  switch v := price.(type) {
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
    start, hasStart := p["start"].(float64)
    maxP, hasMaxP := p["max"].(float64)

    if !hasStart && !hasMaxP {
      continue
    }

    if hasStart {
      totalMin += start
    }
    if hasMaxP {
      totalMax += maxP
      hasMax = true
    } else if hasStart {
      totalMax += start
    }

    if hasStart && hasMaxP {
      parts = append(parts, fmt.Sprintf("%s–%s", formatRp(start), formatRp(maxP)))
    } else if hasStart {
      parts = append(parts, formatRp(start))
    } else if hasMaxP {
      parts = append(parts, formatRp(maxP))
    }
  }

  if len(parts) == 0 {
    return "Rp -"
  }

  priceLine := "Rp " + strings.Join(parts, ", ")

  if len(priceList) > 1 {
    totalStr := ""
    if hasMax {
      totalStr = fmt.Sprintf("%s–%s", formatRp(totalMin), formatRp(totalMax))
    } else {
      totalStr = formatRp(totalMin)
    }
    priceLine += fmt.Sprintf(" (Total: Rp %s)", totalStr)
  }

  return priceLine
}

// FormatTelegramMessage - Updated to use pkg.RedditPost
func FormatTelegramMessage(userQuery string, result *MarketplaceSearch, relevantPosts []pkg.RedditPost) string {
  if result == nil || len(result.Listings) == 0 {
    return fmt.Sprintf("🔍 Terragora Results: %s\n\nNo relevant listings found.", userQuery)
  }

  type pairedItem struct {
    Listing Listing
    Post    pkg.RedditPost
  }

  var paired []pairedItem
  for i, listing := range result.Listings {
    if i < len(relevantPosts) {
      paired = append(paired, pairedItem{Listing: listing, Post: relevantPosts[i]})
    }
  }

  sort.Slice(paired, func(i, j int) bool {
    scoreI := 0.0
    if paired[i].Listing.DealScore != nil {
      scoreI = *paired[i].Listing.DealScore
    }
    scoreJ := 0.0
    if paired[j].Listing.DealScore != nil {
      scoreJ = *paired[j].Listing.DealScore
    }
    return scoreI > scoreJ
  })

  var b strings.Builder

  b.WriteString(fmt.Sprintf("🔍 Terragora Results: %s\n", userQuery))
  b.WriteString(fmt.Sprintf("📊 Found: %d listings | Sorted by: Best Value\n\n", len(paired)))
  b.WriteString("━━━━━━━━━━━━━━━\n\n")

  for i, item := range paired {
    priceStr := FormatPrice(item.Post.Price)

    b.WriteString(fmt.Sprintf("%d. %s\n\n", i+1, item.Post.Title))
    b.WriteString(fmt.Sprintf("💰 Price: %s\n", priceStr))

    if item.Listing.Location != nil {
      b.WriteString(fmt.Sprintf("📍 Location: %s\n", *item.Listing.Location))
    }

    b.WriteString(fmt.Sprintf("📦 Condition: %s\n", item.Listing.Condition))

    if item.Listing.DealScore != nil {
      b.WriteString(fmt.Sprintf("📈 Deal Score: %.1f/10\n", *item.Listing.DealScore))
    }

    b.WriteString("\n📝 Seller Notes:\n")
    for _, note := range item.Listing.SellerNotes {
      b.WriteString(fmt.Sprintf("• %s\n", note))
    }

    watchOut := "-"
    if item.Listing.WatchOut != "" {
      watchOut = item.Listing.WatchOut
    }

    b.WriteString(fmt.Sprintf("\n✅ Verdict: %s\n", item.Listing.Verdict))
    b.WriteString(fmt.Sprintf("⚠️ Watch Out: %s\n\n", watchOut))

    b.WriteString(fmt.Sprintf("🔗 View Post: %s\n\n", item.Listing.URL))
    b.WriteString("━━━━━━━━━━━━━━━\n\n")
  }

  return strings.TrimSpace(b.String())
}

