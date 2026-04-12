package botserver

import (
  "fmt"
  "sort"
  "strings"

  pg "leaddits/internal/pkg/pg"
)

// FormatTelegramMessage constructs the final string for the bot UI
func FormatTelegramMessage(userQuery string, result *MarketplaceSearch, relevantPosts []pg.RedditPost) string {
  if result == nil || len(result.Listings) == 0 {
    return fmt.Sprintf("🔍 Terragora Results: %s\n\nNo relevant listings found.", userQuery)
  }

  var paired []PairedResult
  for i, listing := range result.Listings {
    if i < len(relevantPosts) {
      paired = append(paired, PairedResult{Listing: listing, Post: relevantPosts[i]})
    }
  }

  // Sort by DealScore descending
  sort.Slice(paired, func(i, j int) bool {
    valI, valJ := 0.0, 0.0
    if paired[i].Listing.DealScore != nil {
      valI = *paired[i].Listing.DealScore
    }
    if paired[j].Listing.DealScore != nil {
      valJ = *paired[j].Listing.DealScore
    }
    return valI > valJ
  })

  var b strings.Builder
  b.WriteString(fmt.Sprintf("🔍 Results for: %s\n", userQuery))
  b.WriteString(fmt.Sprintf("📊 Found: %d listings | Best Value\n", len(paired)))
  b.WriteString("━━━━━━━━━━━━━━━\n\n")

  for i, item := range paired {
    b.WriteString(fmt.Sprintf("%d. %s\n", i+1, item.Post.Title))
    b.WriteString(fmt.Sprintf("💰 Price: %s\n", FormatPrice(item.Post.Price)))

    if item.Listing.Location != nil {
      b.WriteString(fmt.Sprintf("📍 Location: %s\n", *item.Listing.Location))
    }

    b.WriteString(fmt.Sprintf("📦 Condition: %s\n", item.Listing.Condition))

    if item.Listing.DealScore != nil {
      b.WriteString(fmt.Sprintf("📈 Deal Score: %.1f/10\n", *item.Listing.DealScore))
    }

    if len(item.Listing.SellerNotes) > 0 {
      b.WriteString("\n📝 Seller Notes:\n")
      for _, note := range item.Listing.SellerNotes {
        b.WriteString(fmt.Sprintf("• %s\n", note))
      }
    }

    verdict := "N/A"
    if item.Listing.Verdict != "" {
      verdict = item.Listing.Verdict
    }
    b.WriteString(fmt.Sprintf("\n✅ Verdict: %s\n", verdict))

    if item.Listing.WatchOut != "" {
      b.WriteString(fmt.Sprintf("⚠️ Watch Out: %s\n", item.Listing.WatchOut))
    }

    url := ""
    if item.Post.URL != nil {
      url = *item.Post.URL
    }
    b.WriteString(fmt.Sprintf("\n🔗 View Post: %s\n", url))
    b.WriteString("━━━━━━━━━━━━━━━\n\n")
  }

  return strings.TrimSpace(b.String())
}
