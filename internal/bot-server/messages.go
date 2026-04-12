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
  // Clean up Title: Remove [WTS], WTS:, etc. (Case-Insensitive)
  cleanTitle := post.Title
  upperTitle := strings.ToUpper(cleanTitle)
  
  // Common prefixes to strip
  prefixes := []string{"[WTS]", "WTS:", "WTS -", "WTS "}
  
  for _, prefix := range prefixes {
    if strings.HasPrefix(upperTitle, prefix) {
      // Slice the original string by the length of the matching prefix
      cleanTitle = cleanTitle[len(prefix):]
      // Update upperTitle in case of multiple prefixes
      upperTitle = strings.ToUpper(cleanTitle)
    }
  }

  // Trim leading/trailing brackets, dashes, colons, and spaces
  cleanTitle = strings.TrimLeft(cleanTitle, " []-:")
  cleanTitle = strings.TrimSpace(cleanTitle)

  // Fallback to original if stripping made it empty
  if cleanTitle == "" {
    cleanTitle = post.Title
  }

  // 1. Title
  b.builder.WriteString(fmt.Sprintf("%d. %s\n", index, cleanTitle))

  // 2. Price
  formattedPrice := FormatPrice(post.Price)
  if formattedPrice != "" && !strings.EqualFold(formattedPrice, "n/a") {
    b.builder.WriteString(fmt.Sprintf("💰 Price: %s\n", formattedPrice))
  }

  // 3. Seller Notes (Pulling directly from DB field)
  if post.Notes != nil && strings.TrimSpace(*post.Notes) != "" {
    b.builder.WriteString("\n📝 Notes:\n")
    b.builder.WriteString(fmt.Sprintf("%s\n", *post.Notes))
  }

  // 4. URL
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

