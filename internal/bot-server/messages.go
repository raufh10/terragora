package botserver

import (
  "fmt"
  "strings"

  pg "leaddits/internal/pkg/pg"
)

type TelegramMessageBuilder struct {
  userQuery string
  posts     []pg.RedditPost
  builder   strings.Builder
}

func NewTelegramMessageBuilder(userQuery string, relevantPosts []pg.RedditPost) *TelegramMessageBuilder {
  return &TelegramMessageBuilder{
    userQuery: userQuery,
    posts:     relevantPosts,
  }
}

func (b *TelegramMessageBuilder) Build() string {
  if len(b.posts) == 0 {
    return fmt.Sprintf("🔍 Results: %s\n\nNo relevant listings found.", b.userQuery)
  }

  b.builder.WriteString(fmt.Sprintf("🔍 Results for: %s\n", b.userQuery))
  b.builder.WriteString(fmt.Sprintf("📊 Found: %d listings\n", len(b.posts)))
  b.builder.WriteString("━━━━━━━━━━━━━━━\n\n")

  for i, post := range b.posts {
    b.addListing(i+1, post)
  }

  return strings.TrimSpace(b.builder.String())
}

func (b *TelegramMessageBuilder) addListing(index int, post pg.RedditPost) {
  // Title
  b.builder.WriteString(fmt.Sprintf("%d. %s\n", index, post.Title))

  // Price
  formattedPrice := FormatPrice(post.Price)
  if formattedPrice != "" && !strings.EqualFold(formattedPrice, "n/a") {
    b.builder.WriteString(fmt.Sprintf("💰 Price: %s\n", formattedPrice))
  }

  // Seller Notes (Pulling directly from DB field)
  if post.Notes != nil && strings.TrimSpace(*post.Notes) != "" {
    b.builder.WriteString("\n📝 Notes:\n")
    // If notes are stored as a block, we just display it. 
    // If you want bullets, you can split by newlines.
    b.builder.WriteString(fmt.Sprintf("%s\n", *post.Notes))
  }

  // URL
  url := ""
  if post.URL != nil {
    url = *post.URL
  }
  b.builder.WriteString(fmt.Sprintf("\n🔗 View Post: %s\n", url))
  b.builder.WriteString("━━━━━━━━━━━━━━━\n\n")
}

func FormatTelegramMessage(userQuery string, relevantPosts []pg.RedditPost) string {
  return NewTelegramMessageBuilder(userQuery, relevantPosts).Build()
}

