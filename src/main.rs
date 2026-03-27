mod config;
mod models;
mod db;
mod scraper;

use crate::config::Config;
use crate::scraper::Scraper;
use crate::db::create_pool;
use crate::db::pgvector::bulk_ingest_raw_posts;
use crate::scraper::extract::RawScrapedPost;
use std::error::Error;

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
  println!("--- 🚀 INITIALIZING SCRAPER 🚀 ---");

  let config = Config::from_env();
  println!("[1/3] Config loaded. Target: {:?}", config.subreddits);

  let pool = create_pool(&config.database_url).await?;
  println!("[2/3] Database connected.");

  let reddit_scraper = Scraper::new(config).await?;
  
  println!("[3/3] Scraping Reddit...");
  let raw_posts: Vec<RawScrapedPost> = reddit_scraper.scrape_all().await?;

  if raw_posts.is_empty() {
    println!("⚠️ No posts found with flairs. Exiting.");
    return Ok(());
  }

  println!("📡 Found {} relevant posts.", raw_posts.len());

  if let Some(post) = raw_posts.first() {
    println!("--- SAMPLE ---");
    println!("Title: {}", post.title);
    println!("ID: {}", post.reddit_id);
    println!("--------------");
  }

  let storable = crate::scraper::extract::process_response_to_storable(raw_posts);

  println!("📥 Ingesting into PostgreSQL...");
  match bulk_ingest_raw_posts(&pool, &storable).await {
    Ok(_) => println!("✅ Done! {} items added/updated.", storable.len()),
    Err(e) => println!("❌ DB Error: {}", e),
  }

  Ok(())
}

