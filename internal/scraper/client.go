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

  "github.com/joho/godotenv"
)

func NewConfig() (*Client, error) {
  _ = godotenv.Load()

  dbURL := os.Getenv("DATABASE_URL")
  scrapeOpsKey := os.Getenv("SCRAPEOPS_API_KEY")

  if dbURL == "" || scrapeOpsKey == "" {
    return nil, fmt.Errorf("DATABASE_URL and SCRAPEOPS_API_KEY must be set")
  }

  agents, err := fetchFreshUserAgents(scrapeOpsKey)
  if err != nil {
    return nil, fmt.Errorf("failed to fetch user agents: %w", err)
  }

  initialUA := agents[rand.Intn(len(agents))]
  proxy, err := generateOxylabsProxy(initialUA.Type)
  if err != nil {
    return nil, fmt.Errorf("failed to configure Oxylabs proxy: %w", err)
  }

  return &Client{
    DatabaseURL: dbURL,
    Targets: Targets{
      BaseURL:    "https://www.reddit.com",
      Subreddits: []string{"jualbeliindonesia"},
    },
    Config: ScraperConfigs{
      UserAgentPool:  agents,
      LastUsedUA:     initialUA.Raw,
      ProxyURL:       proxy,
      TimeoutSeconds: 120 * time.Second,
    },
  }, nil
}

func (c *Client) GetRandomUA() UserAgent {
  if len(c.Config.UserAgentPool) == 0 {
    return UserAgent{Raw: "LeadditsBot/1.0", Type: "windows"}
  }
  return c.Config.UserAgentPool[rand.Intn(len(c.Config.UserAgentPool))]
}

func (c *Client) RotateSession() error {
  var newUA UserAgent

  for i := 0; i < len(c.Config.UserAgentPool); i++ {
    newUA = c.GetRandomUA()
    if newUA.Raw != c.Config.LastUsedUA {
      break
    }
  }

  proxy, err := generateOxylabsProxy(newUA.Type)
  if err != nil {
    return err
  }

  c.Config.ProxyURL = proxy
  c.Config.LastUsedUA = newUA.Raw
  return nil
}

func (c *Client) GetSubredditURL(subreddit string) string {
  return fmt.Sprintf("%s/r/%s.json?limit=100", c.Targets.BaseURL, subreddit)
}

func (c *Client) GetSubredditPaginationURL(subreddit, after string) string {
  return fmt.Sprintf("%s/r/%s.json?limit=100&after=%s", c.Targets.BaseURL, subreddit, after)
}

// --- Client Private Helpers ---

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

func generateOxylabsProxy(platform string) (string, error) {
  user := os.Getenv("OXYLABS_USER")
  key := os.Getenv("OXYLABS_KEY")

  if user == "" || key == "" {
    return "", fmt.Errorf("OXYLABS credentials not set")
  }

  username := url.QueryEscape(user)
  password := url.QueryEscape(key)
  sessionID := rand.Intn(999999-100000) + 100000

  fullUsername := fmt.Sprintf("customer-%s-platform-%s-sessid-%d", username, platform, sessionID)

  return fmt.Sprintf("http://%s:%s@pr.oxylabs.io:7777", fullUsername, password), nil
}

