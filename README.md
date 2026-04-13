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

## Project Layout

```
terragora/
├── cmd/                    # Entrypoints (main.go) for each service
│   ├── bot-server/
│   ├── pipeline/
│   ├── publisher/
│   └── scraper/
│
├── internal/
│   ├── bot-server/
│   ├── pipeline/
│   ├── scraper/
│   └── pkg/                # Shared packages across services
│       ├── llm/            # OpenAI client (embeddings + text processing)
│       ├── nats/           # NATS JetStream client
│       └── pg/             # pgvector / PostgreSQL client
│
├── migrations/             # Database migrations
├── scripts/                # Utility scripts
├── bin/                    # Compiled binaries
│
├── BotServerDockerfile
├── PipelineDockerfile
├── PublisherDockerfile
└── ScraperDockerfile
```

## Architecture Overview

Terragora is built on a **NATS JetStream** backbone. It orchestrates three decoupled services through a producer-consumer architecture.

### 1. Trigger & Orchestration
The system lifecycle begins via two primary triggers:
* **Cron Scheduler:** Initiates routine sweeps on a fixed interval.
* **Database Triggers:** Listens for `INSERT/UPDATE` notifications from a **pgvector** table.
* **Publisher:** Consolidates these triggers and dispatches tasks into the JetStream message queues.

### 2. Service Layer
* **Scraper:** Consumes tasks to ingest Reddit data via the `.json` endpoint. It implements a recursive pagination logic, traversing the `after` keys until specified limit target reached.
* **Data Pipeline:** Processes incoming raw posts through two tracks:
    * **Extraction:** Utilizes `GPT-4.5-mini` to parse unstructured text into structured fields (Price, Seller Notes).
    * **Vectorization:** Generates embeddings using `text-embedding-3-small` and persists them in **pgvector**.
* **Bot Server:** Interfaces with **Telegram** via webhooks. Upon receiving a user query, the server:
    1.  Vectorizes the search string.
    2.  Executes a **cosine similarity** search against the vector store.
    3.  Aggregates the top results into a formatted response containing the title, price, notes, and source URL.
