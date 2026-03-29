use crate::config::Config;
use crate::scraper::Scraper;
use crate::db::create_pool;
use crate::db::pgvector::{fetch_active_reddit_urls, bulk_update_url_statuses};
use crate::models::{RedditUrlStatus, RedditUrlStatuses};
use std::error::Error;
use tokio::time::Duration;
use tokio::time::sleep;

pub async fn run_post_orchestration() -> Result<(), Box<dyn Error>> {
  let config = Config::from_env();
  let pool = create_pool(&config.database_url).await?;
  let active_data = fetch_active_reddit_urls(&pool).await?;

  if active_data.urls.is_empty() {
    println!("ℹ️  No active URLs to verify.");
    return Ok(());
  }

  println!("--- 🔍 VERIFYING {} POSTS ---", active_data.urls.len());
  let reddit_scraper = Scraper::new(config).await?;
  let mut updated_statuses = Vec::new();

  for url in active_data.urls {
    if url.contains("i.redd.it") || url.contains("preview.redd.it") || url.ends_with(".jpg") || url.ends_with(".png") {
      println!("🗑️  [MEDIA] Deactivating: {}", url);
      updated_statuses.push(RedditUrlStatus { url: url.clone(), is_active: false });
      continue;
    }

    let json_url = if url.ends_with(".json") { url.clone() } else { format!("{}.json", url) };

    let is_active = {
      let mut attempts = 0;
      let max_attempts = 3;

      loop {
        match reddit_scraper.scrape_single_url(&json_url).await {
          Ok(posts) => {
            let has_wts = posts.iter().any(|post| {
              post.raw_json.get("link_flair_richtext")
                .and_then(|f| f.as_array())
                .map_or(false, |flairs| {
                  flairs.iter().any(|f| {
                    f.get("t").and_then(|t| t.as_str())
                      .map_or(false, |text| {
                        text.to_ascii_uppercase().contains("WTS")
                      })
                  })
                })
            });

            break if has_wts {
              println!("✅ [ACTIVE] WTS Found: {}", url);
              true
            } else {
              println!("🚫 [REJECT] Not WTS: {}", url);
              false
            };
          }

          Err(e) => {
            let err_msg = e.to_string();

            if err_msg.contains("429") && attempts < max_attempts {
              attempts += 1;
              let backoff = 5 * attempts; // seconds
              println!(
                "🛑 [RATE LIMIT] Retry {}/{} after {}s: {}",
                attempts, max_attempts, backoff, url
              );
              sleep(Duration::from_secs(backoff)).await;
              continue;
            }

            if err_msg.contains("429") {
              println!("❌ [RATE LIMIT FAIL] Skipping after retries: {}", url);
              break false;
            }

            if url.contains("/gallery/") && err_msg.contains("decoding") {
              println!("🏗️  [GALLERY] Decoding Issue (Keeping): {}", url);
              break true;
            }

            println!("❌ [ERROR] {}: {}", err_msg, url);
            break false;
          }
        }
      }
    };

    if let Some(attempts) = Some(3) {
      println!("⏸️ Cooling down for 5s...");
      sleep(Duration::from_secs(5)).await;
    }

    updated_statuses.push(RedditUrlStatus { url, is_active });
    sleep(Duration::from_secs(5)).await;
  }

  let total = updated_statuses.len();
  let deactivated = updated_statuses.iter().filter(|s| !s.is_active).count();
  let status_payload = RedditUrlStatuses { items: updated_statuses };

  println!("\n📥 Syncing {} updates ({} deactivated)...", total, deactivated);
  bulk_update_url_statuses(&pool, &status_payload).await?;
  println!("✨ Sync Complete.");

  Ok(())
}
