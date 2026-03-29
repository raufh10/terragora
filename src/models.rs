use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Deserialize, Serialize)]
pub struct RedditPostData {
  #[serde(rename = "name")]
  pub reddit_id: String,
  pub title: String,
  pub selftext: String,
  pub url: String,
  pub subreddit: String,
  pub created_utc: f64,
  pub link_flair_richtext: Option<Vec<Value>>,
  #[serde(flatten)]
  pub extra_metadata: Value,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct RedditPostChild {
  pub data: RedditPostData,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct RedditData {
  pub children: Vec<RedditPostChild>,
  pub after: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct RedditResponse {
  pub data: RedditData,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct StorablePost {
  pub reddit_id: String,
  pub title: String,
  pub content: String,
  pub url: String,
  pub posted_at: f64,
  pub metadata: Value,
  pub is_active: bool,
}

