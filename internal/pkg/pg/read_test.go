package pkg

import (
  "testing"
)

func TestFormatEmbedding(t *testing.T) {
  tests := []struct {
    name     string
    input    []float32
    expected string
  }{
    {"empty", []float32{}, "[]"},
    {"simple", []float32{0.1, 0.2, 0.3}, "[0.1,0.2,0.3]"},
  }

  for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
      got, err := formatEmbedding(tt.input)
      if err != nil {
        t.Fatalf("unexpected error: %v", err)
      }
      if got != tt.expected {
        t.Errorf("got %s, want %s", got, tt.expected)
      }
    })
  }
}

