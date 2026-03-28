mod config;
mod models;
mod db;
mod scraper;
mod orchestration;

use std::error::Error;

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    println!("🚀 --- STARTING FULL SCRAPING PIPELINE --- 🚀");

    if let Err(e) = orchestration::subreddit::run_subreddit_orchestration().await {
        eprintln!("❌ Subreddit Orchestration failed: {}", e);
    }

    println!("\n------------------------------------------\n");

    if let Err(e) = orchestration::post::run_post_orchestration().await {
        eprintln!("❌ Post Orchestration failed: {}", e);
    }

    println!("\n✨ --- ALL TASKS COMPLETE --- ✨");
    Ok(())
}

