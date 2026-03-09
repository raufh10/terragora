# Rust Reddit Scraper (RAG-Ready) 🦀🚀

A high-performance Rust engine designed to scrape Reddit data, bypass ISP blocks (like Internet Positif), and ingest raw data into a PostgreSQL/pgvector database for RAG (Retrieval-Augmented Generation) processing.

## 🛠 Features
- **Fastly IP Pinning:** Bypasses DNS hijacking by mapping `www.reddit.com` directly to Fastly's CDN IP.
- **TLS Handshake Bypass:** Uses `rustls` to avoid system-level certificate interference.
- **Memory-Safe Extraction:** Uses Rust's type system to parse nested JSON without overhead.
- **Bulk Ingestion:** Uses `sqlx` and `UNNEST` for high-speed database upserts.
- **Python-Friendly:** Stores the complete raw JSON in a `metadata` column for flexible downstream processing.

## 📁 Project Structure
- `src/main.rs`: Orchestrates the flow and provides detailed logs.
- `src/config.rs`: Environment management and URL construction.
- `src/models.rs`: Reddit API data structures.
- `src/scraper/`: The request engine and data extraction logic.
- `src/db/`: PostgreSQL connection and `pgvector` operations.

## 🚀 Setup & Deployment

### 1. Environment Variables
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgres://user:password@host:port/dbname
SUBREDDITS=jualbeliindonesia
