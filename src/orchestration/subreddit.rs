use crate::config::Config;
use crate::scraper::Scraper;
use crate::db::create_pool;
use crate::db::pgvector::bulk_ingest_raw_posts;
use crate::scraper::extract::{RawScrapedPost, process_response_to_storable};
use std::error::Error;

pub async fn run_subreddit_orchestration() -> Result<(), Box<dyn Error>> {
    println!("--- 🚀 INITIALIZING SCRAPER 🚀 ---");

    // Step 1: Load config
    let config = match Config::from_env() {
        cfg => {
            println!("[1/3] Config loaded. Target: {:?}", cfg.subreddits);
            cfg
        }
    };

    // Step 2: Connect to database
    let pool = match create_pool(&config.database_url).await {
        Ok(p) => {
            println!("[2/3] Database connected.");
            p
        }
        Err(e) => {
            eprintln!("❌ Failed to connect to database: {}", e);
            return Err(Box::new(e));
        }
    };

    // Step 3: Initialize Reddit scraper
    let reddit_scraper = match Scraper::new(config).await {
        Ok(scraper) => {
            println!("[3/3] Scraper initialized.");
            scraper
        }
        Err(e) => {
            eprintln!("❌ Failed to initialize scraper: {}", e);
            return Err(e);
        }
    };

    // Step 4: Scrape all subreddits
    println!("📡 Scraping Reddit...");
    let raw_posts: Vec<RawScrapedPost> = match reddit_scraper.scrape_all().await {
        Ok(posts) => posts,
        Err(e) => {
            eprintln!("❌ Error during scraping: {}", e);
            return Err(e);
        }
    };

    if raw_posts.is_empty() {
        println!("⚠️ No posts found with target flairs. Exiting.");
        return Ok(());
    }

    println!("📈 Found {} relevant posts.", raw_posts.len());

    if let Some(post) = raw_posts.first() {
        println!("--- SAMPLE POST ---");
        println!("Title: {}", post.title);
        println!("ID: {}", post.reddit_id);
        println!("------------------");
    }

    // Step 5: Process posts for storage
    let storable = process_response_to_storable(raw_posts);

    // Step 6: Ingest into database
    println!("📥 Ingesting into PostgreSQL...");
    if let Err(e) = bulk_ingest_raw_posts(&pool, &storable).await {
        eprintln!("❌ Failed to ingest posts into DB: {}", e);
        return Err(Box::new(e));
    }

    println!("✅ Done! {} items added/updated.", storable.len());
    Ok(())
}
