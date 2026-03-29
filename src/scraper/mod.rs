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
      config.proxy_url.clone(),
      config.reddit_static_ip
    ).await?;

    Ok(Self { 
      client, 
      config 
    })
  }

  pub fn get_client(&self) -> &reqwest::Client {
    &self.client
  }
}

