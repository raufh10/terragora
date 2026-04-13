# Terragora

A Telegram chatbot that helps you find used item deals sourced from the r/jualbeliindonesia subreddit.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Go |
| Database | pgvector |
| Messaging | NATS JetStream |
| Embeddings | OpenAI text-embedding-3-small |
| Text Processing | OpenAI GPT-4.5-mini |
| Deployment | Railway (Dockerfile) |

## Architecture Overview

Terragora is built around a NATS JetStream messaging backbone that coordinates three independent services: a scraper, a data pipeline, and a bot server.

A cron job and pgvector table notifications act as the system's triggers — the cron fires on a schedule, while pgvector notifies on row insert/update. Both feed into a central publisher that pushes tasks onto JetStream queues.

The scraper consumes tasks from the queue, fetches posts from Reddit using the `.json` endpoint, and handles pagination by looping over `after` keys until all pages are collected.

The data pipeline runs two parallel pipelines per post: one extracts structured fields (price & seller"s notes) from raw post text using GPT-4.5-mini, and another generates a vector embedding using text-embedding-3-small and stores it in pgvector.

The bot server connects to Telegram via webhook. When a search query arrives, it vectorizes the query, runs a cosine similarity search against stored post embeddings, then builds and returns a message with the most relevant results including title, price, notes, and URL.

## Project Layout

```
terragora/
├── cmd/                        # Entrypoints (main.go) for each service
│   ├── bot-server/
│   ├── pipeline/
│   ├── publisher/
│   └── scraper/
│
├── internal/                   # Private application code
│   ├── bot-server/
│   ├── pipeline/
│   ├── scraper/
│   └── pkg/                    # Shared packages across services
│       ├── llm/                # OpenAI client (embeddings + text processing)
│       ├── nats/               # NATS JetStream client
│       └── pg/                 # pgvector / PostgreSQL client
│
├── migrations/                 # Database migrations
├── scripts/                    # Utility scripts
├── bin/                        # Compiled binaries
│
├── BotServerDockerfile
├── PipelineDockerfile
├── PublisherDockerfile
└── ScraperDockerfile
```
