package scraper

import (
  "fmt"
  "math/rand"
  "os"
  "time"

  "github.com/joho/godotenv"
)

// NewConfig initializes the scraper client by fetching UAs and setting up proxies.
func NewConfig() (*Client, error) {
  _ = godotenv.Load()

  scrapeOpsKey := os.Getenv("SCRAPEOPS_API_KEY")
  if scrapeOpsKey == "" {
    return nil, fmt.Errorf("SCRAPEOPS_API_KEY must be set")
  }

  agents, err := fetchFreshUserAgents(scrapeOpsKey)
  if err != nil {
    return nil, fmt.Errorf("failed to fetch user agents: %w", err)
  }

  if len(agents) == 0 {
    return nil, fmt.Errorf("no user agents returned from provider")
  }

  initialUA := agents[rand.Intn(len(agents))]
  proxy, err := generateOxylabsProxy(initialUA.Type)
  if err != nil {
    return nil, fmt.Errorf("failed to configure Oxylabs proxy: %w", err)
  }

  return &Client{
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

  for i := 0; i < 10; i++ {
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

func (c *Client) GetSubredditURL(subreddit string, limit int) string {
  return fmt.Sprintf("%s/r/%s.json?limit=%d", c.Targets.BaseURL, subreddit, limit)
}

func (c *Client) GetSubredditPaginationURL(subreddit, after string, limit int) string {
  return fmt.Sprintf("%s/r/%s.json?limit=%d&after=%s", c.Targets.BaseURL, subreddit, limit, after)
}

