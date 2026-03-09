use reqwest::header::{HeaderMap, HeaderValue, USER_AGENT};
use serde::Deserialize;
use std::net::SocketAddr;
use std::time::Duration;

#[derive(Deserialize, Debug)]
struct RedditResponse {
  data: RedditData,
}

#[derive(Deserialize, Debug)]
struct RedditData {
  children: Vec<Child>,
}

#[derive(Deserialize, Debug)]
struct Child {
  data: PostData,
}

#[derive(Deserialize, Debug)]
struct PostData {
  title: String,
}

async fn fetch_titles(client: &reqwest::Client, label: &str, url: &str) -> Result<(), Box<dyn std::error::Error>> {
  let mut headers = HeaderMap::new();
  headers.insert(USER_AGENT, HeaderValue::from_static("Mozilla/5.0 Chrome/122.0.0.0"));

  let response = client.get(url).headers(headers).send().await?;

  if response.status().is_success() {
    let json_data: RedditResponse = response.json().await?;
    println!("\n--- {} ---", label);
    for (i, post) in json_data.data.children.iter().take(25).enumerate() {
      println!("{}. {}", i + 1, post.data.title);
    }
  } else {
    println!("Failed to fetch {}: {}", label, response.status());
  }
  Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
  let reddit_ip: SocketAddr = "151.101.129.140:443".parse()?;
  let client = reqwest::Client::builder()
    .resolve("www.reddit.com", reddit_ip)
    .resolve("reddit.com", reddit_ip)
    .timeout(Duration::from_secs(15))
    .build()?;

  // URL Variations:
  // New:       /new.json
  // Top Week:  /top.json?t=week
  // Top Month: /top.json?t=month
  // Best:      /best.json
  
  let new_url = "https://www.reddit.com/r/rust/new.json";
  let top_week_url = "https://www.reddit.com/r/rust/top.json?t=week";

  fetch_titles(&client, "LATEST NEW POSTS", new_url).await?;
  fetch_titles(&client, "TOP POSTS THIS WEEK", top_week_url).await?;

  Ok(())
}

