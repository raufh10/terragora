package scraper

import (
  "encoding/json"
  "fmt"
  "net/http"
  "net/url"
  "time"
)

// InitHttpClient creates a reusable client configured with your Oxylabs proxy.
// We return a pointer to http.Client which is thread-safe and designed for reuse.
func (c *Client) InitHttpClient() (*http.Client, error) {
  proxyURL, err := url.Parse(c.Config.ProxyURL)
  if err != nil {
    return nil, fmt.Errorf("invalid proxy URL: %w", err)
  }

  transport := &http.Transport{
    Proxy: http.ProxyURL(proxyURL),
    // Performance tuning for concurrent scraping
    MaxIdleConns:          100,
    IdleConnTimeout:       90 * time.Second,
    TLSHandshakeTimeout:   10 * time.Second,
    ExpectContinueTimeout: 1 * time.Second,
  }

  return &http.Client{
    Transport: transport,
    Timeout:   c.Config.TimeoutSeconds,
  }, nil
}

// FetchSubredditJson performs the GET request and returns a generic JSON map.
func (c *Client) FetchSubredditJson(httpClient *http.Client, targetURL string, ua UserAgent) (map[string]interface{}, error) {
  req, err := http.NewRequest("GET", targetURL, nil)
  if err != nil {
    return nil, err
  }

  // Set the identity headers
  req.Header.Set("User-Agent", ua.Raw)
  req.Header.Set("Accept", "application/json")

  resp, err := httpClient.Do(req)
  if err != nil {
    return nil, fmt.Errorf("request failed: %w", err)
  }
  defer resp.Body.Close()

  // Sanity check on status code
  if resp.StatusCode != http.StatusOK {
    return nil, fmt.Errorf("Reddit API Error: Status %d", resp.StatusCode)
  }

  // Decode into a generic map
  var result map[string]interface{}
  if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
    return nil, fmt.Errorf("failed to decode raw JSON: %w", err)
  }

  return result, nil
}

