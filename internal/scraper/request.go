package scraper

import (
  "encoding/json"
  "fmt"
  "net/http"
  "net/url"
  "time"
)

// Initialize http client for scraping with ProxyURL
func (c *Client) InitHttpClient() (*http.Client, error) {
  transport := &http.Transport{
    MaxIdleConns:          100,
    IdleConnTimeout:       90 * time.Second,
    TLSHandshakeTimeout:   10 * time.Second,
    ExpectContinueTimeout: 1 * time.Second,
  }

  if c.Config.ProxyURL != "" {
    proxyURL, err := url.Parse(c.Config.ProxyURL)
    if err != nil {
      return nil, fmt.Errorf("invalid proxy URL: %w", err)
    }
    transport.Proxy = http.ProxyURL(proxyURL)
  }

  return &http.Client{
    Transport: transport,
    Timeout:   c.Config.TimeoutSeconds,
  }, nil
}

// Fetch SubredditJson data (scrape reddit)
func (c *Client) FetchSubredditJson(httpClient *http.Client, targetURL string, ua UserAgent) (*RedditResponse, error) {
  req, err := http.NewRequest("GET", targetURL, nil)
  if err != nil {
    return nil, err
  }

  req.Header.Set("User-Agent", ua.Raw)
  req.Header.Set("Accept", "application/json")

  resp, err := httpClient.Do(req)
  if err != nil {
    return nil, fmt.Errorf("request failed: %w", err)
  }
  defer resp.Body.Close()

  if resp.StatusCode != http.StatusOK {
    return nil, fmt.Errorf("Reddit API Error: Status %d", resp.StatusCode)
  }

  var result RedditResponse
  if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
    return nil, fmt.Errorf("failed to decode reddit response: %w", err)
  }

  return &result, nil
}
