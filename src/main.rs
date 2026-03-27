mod config;
mod models;
mod db;
mod scraper;
mod orchestration;

use std::error::Error;

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
  orchestration::subreddit::run_subreddit_orchestration().await
}

