package pkg

import (
  "fmt"

  "github.com/nats-io/nats.go"
)

type Handler func(msg *nats.Msg)

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
