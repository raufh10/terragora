package pkg

import (
  "fmt"
  "time"

  "github.com/lib/pq"
)

type EventCallback func(payload string)

func ListenForEvents(dbURL string, channel string, callback EventCallback) error {
  reportErr := func(ev pq.ListenerEventType, err error) {
    if err != nil {
      fmt.Printf("[-] Postgres Listener Error (%v): %v\n", ev, err)
    }
  }

  listener := pq.NewListener(dbURL, 10*time.Second, time.Minute, reportErr)

  err := listener.Listen(channel)
  if err != nil {
    return fmt.Errorf("failed to listen on channel %s: %w", channel, err)
  }

  fmt.Printf("[+] Database listener active on channel: %s\n", channel)

  go func() {
    for {
      select {
      case notification := <-listener.Notify:
        if notification == nil {
          continue
        }
        callback(notification.Extra)
      case <-time.After(90 * time.Second):
        go listener.Ping()
      }
    }
  }()

  return nil
}
