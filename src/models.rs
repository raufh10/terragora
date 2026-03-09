use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct RedditResponse {
  pub data: RedditData,
}

#[derive(Debug, Deserialize)]
pub struct RedditData {
  pub children: Vec<RedditPostChild>,
}

#[derive(Debug, Deserialize)]
pub struct RedditPostChild {
  pub data: RedditPostData,
}

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

