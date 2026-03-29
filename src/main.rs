mod config;
mod models;
mod db;
mod scraper;

use crate::config::Config;
use crate::scraper::Scraper;
use crate::scraper::request::fetch_subreddit_json;
use crate::scraper::extract::process_response;
use crate::db::pgvector::bulk_ingest_raw_posts;
use sqlx::postgres::PgPoolOptions;
use std::error::Error;
use tokio::time::{sleep, Duration};

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
  println!("🚀 --- STARTING REDDIT SCRAPER PIPELINE --- 🚀");

  // 1. Setup Config
  let config = Config::from_env();
  println!("[1/3] Config loaded. Target subreddits: {:?}", config.subreddits);

  // 2. Connect to Database
  let pool = PgPoolOptions::new()
    .max_connections(5)
    .connect(&config.database_url)
    .await?;
  println!("[2/3] Database connected.");

  // 3. Initialize Scraper
  let scraper = Scraper::new(config).await?;
  println!("[3/3] Scraper initialized with proxy.");

  // 4. Subreddit Loop
  for subreddit in &scraper.config.subreddits {
    println!("\n📡 Processing /r/{}...", subreddit);
    
    let mut current_after: Option<String> = None;
    let max_pages = 10;

    for page in 1..=max_pages {
      println!("📄 Page {}/{} (after: {:?})", page, max_pages, current_after);

      let url = match &current_after {
        Some(token) => scraper.config.get_subreddit_pagination_url(subreddit, token),
        None => scraper.config.get_subreddit_url(subreddit),
      };

      // Fetch JSON from Reddit
      let response = fetch_subreddit_json(
        scraper.get_client(), 
        &url,
        &scraper.config.user_agent
      ).await?;

      // Capture pagination token for next iteration
      current_after = response.data.after.clone();

      // Process and Filter (WTS check happens here)
      let storable_posts = process_response(response);

      if storable_posts.is_empty() {
        println!("⚠️ No posts found on this page. Moving to next subreddit.");
        break;
      }

      // Ingest to Postgres
      println!("📥 Ingesting {} posts into DB...", storable_posts.len());
      bulk_ingest_raw_posts(&pool, &storable_posts).await?;

      // Early exit if no more pages
      if current_after.is_none() {
        println!("✅ Reached the end of /r/{}.", subreddit);
        break;
      }

      // Polite delay between pages
      if page < max_pages {
        println!("💤 Sleeping 60s to prevent rate limits...");
        sleep(Duration::from_secs(60)).await;
      }
    }
  }

  println!("\n✨ --- ALL TASKS COMPLETE --- ✨");
  Ok(())
}

// Ensure your Scraper struct has this getter in src/scraper/mod.rs:
// impl Scraper { pub fn get_client(&self) -> &reqwest::Client { &self.client } }

