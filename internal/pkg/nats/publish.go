package pkg

import (
  "encoding/json"
)

func (c *Client) PublishScraperEvent(subject string, event ScraperEvent) error {
  data, err := json.Marshal(event)
  if err != nil {
    return err
  }

  return c.Conn.Publish(subject, data)
}
