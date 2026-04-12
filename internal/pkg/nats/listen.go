package pkg

import (
  "fmt"
  "encoding/json"
  "log"

  "github.com/nats-io/nats.go"
)

type Handler func(msg *nats.Msg)

// Listen subscribes to a NATS subject asynchronously after verifying the connection state
func (c *Client) Listen(subject string, handler Handler) (*nats.Subscription, error) {
  if c.Conn == nil {
    return nil, fmt.Errorf("nats connection is not initialized")
  }

  sub, err := c.Conn.Subscribe(subject, func(m *nats.Msg) {
    handler(m)
  })

  if err != nil {
    return nil, fmt.Errorf("failed to subscribe to %s: %w", subject, err)
  }

  return sub, nil
}

// SubscribeToPipeline handles unmarshaling the batch of events automatically
func (c *Client) SubscribeToPipeline(subject string, handler func([]PipelineEvent)) error {
  _, err := c.Listen(subject, func(m *nats.Msg) {
    var batch []PipelineEvent
    if err := json.Unmarshal(m.Data, &batch); err != nil {
      log.Printf("[!] Failed to unmarshal pipeline batch: %v", err)
      return
    }
    handler(batch)
  })
  return err
}

