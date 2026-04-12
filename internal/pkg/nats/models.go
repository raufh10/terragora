package pkg

type ScraperEvent struct {
  Pages     int    `json:"pages"`
  Limit     int    `json:"limit"`
  Target    string `json:"target"`
  Timestamp string `json:"timestamp"`
}
