use reqwest::{header::{HeaderMap, HeaderValue, USER_AGENT}, Proxy};
use crate::models::RedditResponse;
use std::net::SocketAddr;
use std::time::Duration;
use dotenvy::dotenv;
use std::env;

pub async fn init_client(
  timeout: u64, 
  proxy_url: String,
  reddit_ip: SocketAddr
) -> Result<reqwest::Client, Box<dyn std::error::Error>> {
  dotenv().ok();

  let is_production = env::var("ENV").unwrap_or_default() == "production";
  let proxy = Proxy::all(proxy_url)?;

  let mut builder = reqwest::Client::builder()
    .use_rustls_tls()
    .proxy(proxy)
    .timeout(Duration::from_secs(timeout));

  if !is_production {
    builder = builder
      .resolve("www.reddit.com", reddit_ip)
      .resolve("reddit.com", reddit_ip);
  }

  let client = builder.build()?;

  Ok(client)
}

pub async fn fetch_subreddit_json(
  client: &reqwest::Client, 
  url: &str,
  user_agent: &str
) -> Result<RedditResponse, Box<dyn std::error::Error>> {
  let mut headers = HeaderMap::new();
  headers.insert(USER_AGENT, HeaderValue::from_str(user_agent)?);

  let response = client
    .get(url)
    .headers(headers)
    .send()
    .await?;

  if response.status().is_success() {
    let json_data = response.json::<RedditResponse>().await?;
    Ok(json_data)
  } else {
    Err(format!("ISP/Reddit Error: Status {}", response.status()).into())
  }
}

