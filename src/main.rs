mod config;
mod models;
mod db;
mod scraper;
mod orchestration;

use std::error::Error;
use tokio::time::{sleep, Duration};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
  println!("🚀 --- STARTING FULL SCRAPING PIPELINE --- 🚀");

  if let Err(e) = orchestration::subreddit::run_subreddit_orchestration().await {
    eprintln!("❌ Subreddit Orchestration failed: {}", e);
  }

  println!("⏸ Waiting 30 seconds before starting post orchestration...");
  sleep(Duration::from_secs(30)).await;

  if let Err(e) = orchestration::post::run_post_orchestration().await {
    eprintln!("❌ Post Orchestration failed: {}", e);
  }

  println!("\n✨ --- ALL TASKS COMPLETE --- ✨");
  Ok(())
}
