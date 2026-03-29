pub mod request;
pub mod extract;

use crate::config::Config;
use crate::models::StorablePost;
use std::error::Error;

pub struct Scraper {
  client: reqwest::Client,
  pub config: Config,
}

impl Scraper {
  pub async fn new(config: Config) -> Result<Self, Box<dyn Error>> {
    let client = request::init_client(
      config.timeout_seconds, 
      config.proxy_url.clone(),
      config.reddit_static_ip
    ).await?;

    Ok(Self { 
      client, 
      config 
    })
  }

  pub async fn scrape_all(&self) -> Result<Vec<StorablePost>, Box<dyn Error>> {
    let mut all_results = Vec::new();

    for sub in &self.config.subreddits {
      let url = self.config.get_subreddit_url(sub);

      let response = request::fetch_subreddit_json(
        &self.client, 
        &url, 
        &self.config.user_agent
      ).await?;

      let mut posts = extract::process_response(response);
      all_results.append(&mut posts);
    }

    Ok(all_results)
  }
}
