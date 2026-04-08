package botserver

import (
  llm "leaddits/internal/pkg/llm"
  pg "leaddits/internal/pkg/pg"
)

// Update represents a Telegram incoming webhook update
type Update struct {
  Message struct {
    Chat struct {
      ID int64 `json:"id"`
    } `json:"chat"`
    From struct {
      Username string `json:"username"`
    } `json:"from"`
    Text string `json:"text"`
  } `json:"message"`
}

// PairedResult now uses the LLM package's version of Listing
type PairedResult struct {
  Listing llm.Listing
  Post    pg.RedditPost
}

