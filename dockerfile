# --- Build Stage ---
FROM rust:1.94 as builder
WORKDIR /usr/src/app
COPY . .

# Build for release
RUN cargo build --release

# --- Run Stage ---
FROM debian:bookworm-slim

# Install SSL certificates (needed for Reddit/HTTPS)
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/bin
COPY --from=builder /usr/src/app/target/release/rust_scraper .
CMD ["./rust_scraper"]

