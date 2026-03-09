# --- Build Stage ---
FROM rust:1.94-bookworm as builder
WORKDIR /usr/src/app
COPY . .

# Build for release
ENV DATABASE_URL=postgresql://postgres:ip9wiz0gigp74i053nvimm67nw8xjpf4@ballast.proxy.rlwy.net:33248/railway
RUN cargo build --release

# --- Run Stage ---
FROM debian:bookworm-slim

# Install SSL certificates (needed for Reddit/HTTPS)
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/bin
COPY --from=builder /usr/src/app/target/release/rust_scraper .
CMD ["./rust_scraper"]

