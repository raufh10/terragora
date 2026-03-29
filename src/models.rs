use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize)]
pub struct RedditPostData {
  #[serde(rename = "name")]
  pub reddit_id: String,
  pub title: String,
  pub selftext: String,
  pub url: String,
  pub subreddit: String,
  pub created_utc: f64,
  pub link_flair_richtext: Option<Vec<serde_json::Value>>,
  #[serde(flatten)]
  pub extra_metadata: serde_json::Value,
}

#[derive(Debug, Deserialize)]
pub struct RedditPostChild {
  pub data: RedditPostData,
}

#[derive(Debug, Deserialize)]
pub struct RedditData {
  pub children: Vec<RedditPostChild>,
  pub after: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct RedditResponse {
  pub data: RedditData,
}

#[allow(dead_code)]
pub struct RawScrapedPost {
  pub reddit_id: String,
  pub title: String,
  pub selftext: String,
  pub url: String,
  pub created_utc: f64,
  pub subreddit: String,
  pub raw_json: Value,
}

pub struct StorablePost {
  pub reddit_id: String,
  pub title: String,
  pub content: String,
  pub url: String,
  pub created_at: f64,
  pub raw_json: Value,
}
