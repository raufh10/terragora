package security

import (
  "sync"
  "time"
)

var (
  // lastSeen stores the last timestamp a chatID was processed
  lastSeen = make(map[int64]time.Time)
  mu       sync.Mutex
)

// IsRateLimited checks if a chatID is sending messages faster than the 1-second threshold.
func IsRateLimited(chatID int64) bool {
  mu.Lock()
  defer mu.Unlock()

  now := time.Now()
  last, exists := lastSeen[chatID]
  
  if exists && now.Sub(last) < 1*time.Second {
    return true
  }

  lastSeen[chatID] = now
  return false
}
