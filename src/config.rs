use dotenvy::dotenv;
use std::env;

pub struct Config {
  pub database_url: String,
  pub user_agent: String,
  pub subreddits: Vec<String>,
  pub timeout_seconds: u64,
  pub base_url: String,
}

impl Config {
  pub fn from_env() -> Self {
    dotenv().ok();

    Self {
      database_url: env::var("DATABASE_URL").expect("DATABASE_URL must be set"),
      // Modern Chrome 145 User-Agent (March 2026)
      user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36".to_string(),
      subreddits: vec!["jualbeliindonesia".to_string()],
      timeout_seconds: 15,
      base_url: "https://www.reddit.com".to_string(),
    }
  }

  pub fn get_subreddit_url(&self, subreddit: &str) -> String {
    // Appends .json to the subreddit path to bypass API key requirements
    format!("{}/r/{}.json?limit=100", self.base_url, subreddit)
  }
}

