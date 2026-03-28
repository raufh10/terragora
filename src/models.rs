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
}

#[derive(Debug, Deserialize)]
pub struct RedditResponse {
  pub data: RedditData,
}

#[derive(Debug, Deserialize)]
pub struct RedditUrlResponse(pub Vec<RedditResponse>);

impl RedditUrlResponse {
  pub fn get_post(&self) -> Option<&RedditPostData> {
    Some(&self.0.first()?.data.children.first()?.data)
  }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RedditUrls {
  pub urls: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RedditUrlStatus {
  pub url: String,
  pub is_active: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RedditUrlStatuses {
  pub items: Vec<RedditUrlStatus>,
}


