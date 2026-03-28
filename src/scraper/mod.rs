pub mod request;
pub mod extract;

use crate::config::Config;
use std::error::Error;

pub struct Scraper {
  client: reqwest::Client,
  pub config: Config,
}

impl Scraper {
  pub async fn new(config: Config) -> Result<Self, Box<dyn Error>> {
    let client = request::init_client(
      config.timeout_seconds, 
      config.proxy_url.clone()
    ).await?;

    Ok(Self { 
      client, 
      config 
    })
  }

  pub async fn scrape_all(&self) -> Result<Vec<extract::RawScrapedPost>, Box<dyn Error>> {
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

  pub async fn scrape_single_url(&self, url: &str) -> Result<Vec<extract::RawScrapedPost>, Box<dyn Error>> {
    let response = request::fetch_subreddit_json_as_url(
      &self.client, 
      url, 
      &self.config.user_agent
    ).await?;

    Ok(extract::process_url_response(response))
  }
}

