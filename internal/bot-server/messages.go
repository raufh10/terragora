package botserver

import (
  "fmt"
  "strings"

  llm "leaddits/internal/pkg/llm"
  pg "leaddits/internal/pkg/pg"
)

type TelegramMessageBuilder struct {
  userQuery string
  paired    []PairedResult
  builder   strings.Builder
}

func NewTelegramMessageBuilder(userQuery string, result *llm.MarketplaceSearch, relevantPosts []pg.RedditPost) *TelegramMessageBuilder {
  var paired []PairedResult
  if result != nil {
    for i, listing := range result.Listings {
      if i < len(relevantPosts) {
        paired = append(paired, PairedResult{
          Listing: listing,
          Post:    relevantPosts[i],
        })
      }
    }
  }

  return &TelegramMessageBuilder{
    userQuery: userQuery,
    paired:    paired,
  }
}

func (b *TelegramMessageBuilder) Build() string {
  if len(b.paired) == 0 {
    return fmt.Sprintf("🔍 Results: %s\n\nNo relevant listings found.", b.userQuery)
  }

  b.builder.WriteString(fmt.Sprintf("🔍 Results for: %s\n", b.userQuery))
  b.builder.WriteString(fmt.Sprintf("📊 Found: %d listings\n", len(b.paired)))
  b.builder.WriteString("━━━━━━━━━━━━━━━\n\n")

  for i, item := range b.paired {
    b.addListing(i+1, item)
  }

  return strings.TrimSpace(b.builder.String())
}

func (b *TelegramMessageBuilder) addListing(index int, item PairedResult) {

  // Title
  b.builder.WriteString(fmt.Sprintf("%d. %s\n", index, item.Post.Title))

  // Adjustable: Price
  formattedPrice := FormatPrice(item.Post.Price)
  if formattedPrice != "" && !strings.EqualFold(formattedPrice, "n/a") {
    b.builder.WriteString(fmt.Sprintf("💰 Price: %s\n", formattedPrice))
  }

  // Adjustable: Seller Notes
  if len(item.Listing.SellerNotes) > 0 {
    hasContent := false
    for _, note := range item.Listing.SellerNotes {
      trimmed := strings.TrimSpace(note)
      if trimmed != "" {
        if !hasContent {
          b.builder.WriteString("\n📝 Seller Notes:\n")
          hasContent = true
        }
        b.builder.WriteString(fmt.Sprintf("• %s\n", trimmed))
      }
    }
  }

  // URL
  url := ""
  if item.Post.URL != nil {
    url = *item.Post.URL
  }
  b.builder.WriteString(fmt.Sprintf("\n🔗 View Post: %s\n", url))

  b.builder.WriteString("━━━━━━━━━━━━━━━\n\n")
}

func FormatTelegramMessage(userQuery string, result *llm.MarketplaceSearch, relevantPosts []pg.RedditPost) string {
  return NewTelegramMessageBuilder(userQuery, result, relevantPosts).Build()
}
