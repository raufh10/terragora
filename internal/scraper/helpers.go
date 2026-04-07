package scraper

import (
  "encoding/json"
  "fmt"
  "math/rand"
  "net/http"
  "net/url"
  "os"
  "strings"
  "time"
)

// fetchFreshUserAgents retrieves a list of UAs from ScrapeOps.
func fetchFreshUserAgents(apiKey string) ([]UserAgent, error) {
  apiURL := fmt.Sprintf("http://headers.scrapeops.io/v1/user-agents?api_key=%s&num_results=5", apiKey)

  resp, err := http.Get(apiURL)
  if err != nil {
    return nil, err
  }
  defer resp.Body.Close()

  if resp.StatusCode != http.StatusOK {
    return nil, fmt.Errorf("scrapeops api status: %d", resp.StatusCode)
  }

  var data struct {
    Result []string `json:"result"`
  }

  if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
    return nil, err
  }

  var parsedAgents []UserAgent
  for _, uaStr := range data.Result {
    parsedAgents = append(parsedAgents, UserAgent{
      Raw:  uaStr,
      Type: parseOSType(uaStr),
    })
  }

  return parsedAgents, nil
}

// parseOSType categorizes a UA string into a platform type.
func parseOSType(ua string) string {
  ua = strings.ToLower(ua)
  switch {
  case strings.Contains(ua, "android"):
    return "android"
  case strings.Contains(ua, "iphone") || strings.Contains(ua, "ipad"):
    return "ios"
  case strings.Contains(ua, "windows"):
    return "windows"
  case strings.Contains(ua, "macintosh") || strings.Contains(ua, "mac os x"):
    return "macos"
  case strings.Contains(ua, "linux"):
    return "linux"
  default:
    return "windows"
  }
}

// generateOxylabsProxy builds the authenticated proxy string.
func generateOxylabsProxy(platform string) (string, error) {
  user := os.Getenv("OXYLABS_USER")
  key := os.Getenv("OXYLABS_KEY")

  if user == "" || key == "" {
    return "", fmt.Errorf("OXYLABS credentials not set")
  }

  username := url.QueryEscape(user)
  password := url.QueryEscape(key)
  sessionID := rand.Intn(999999-100000) + 100000

  fullUsername := fmt.Sprintf("customer-%s-sessid-%d", username, sessionID)

  return fmt.Sprintf("http://%s:%s@pr.oxylabs.io:7777", fullUsername, password), nil
}

// getBackoffDuration returns 10s, 20s, or 30s based on attempt number
func GetBackoffDuration(attempt int) time.Duration {
  switch attempt {
  case 1:
    return 10 * time.Second
  case 2:
    return 20 * time.Second
  case 3:
    return 30 * time.Second
  default:
    return 10 * time.Second
  }
}
