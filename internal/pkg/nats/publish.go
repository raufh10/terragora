package pkg

import (
  "encoding/json"
)

// PublishScraperEvent handles the single trigger event for the scraper
func (c *Client) PublishScraperEvent(subject string, event ScraperEvent) error {
  data, err := json.Marshal(event)
  if err != nil {
    return err
  }
  return c.Conn.Publish(subject, data)
}

// PublishPipelineBatch sends a slice of pipeline events to NATS
func (c *Client) PublishPipelineBatch(subject string, events []PipelineEvent) error {
  if len(events) == 0 {
    return nil
  }

  data, err := json.Marshal(events)
  if err != nil {
    return err
  }

  return c.Conn.Publish(subject, data)
}
