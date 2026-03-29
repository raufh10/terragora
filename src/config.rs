use dotenvy::dotenv;
use std::env;
use std::net::SocketAddr;
use fake_user_agent::get_rua;
use urlencoding::encode;

pub struct Config {
  pub database_url: String,
  pub user_agent: String,
  pub subreddits: Vec<String>,
  pub timeout_seconds: u64,
  pub base_url: String,
  pub proxy_url: String,
  pub reddit_static_ip: SocketAddr,
}

impl Config {
  pub fn from_env() -> Self {
    dotenv().ok();

    let proxy_url = Self::generate_oxylabs_proxy().expect("Failed to configure Oxylabs proxy");
    
    let reddit_static_ip: SocketAddr = "151.101.129.140:443"
      .parse()
      .expect("Invalid static Reddit IP address");

    Self {
      database_url: env::var("DATABASE_URL").expect("DATABASE_URL must be set"),
      user_agent: get_rua().to_string(),
      subreddits: vec!["jualbeliindonesia".to_string()],
      timeout_seconds: 120,
      base_url: "https://www.reddit.com".to_string(),
      proxy_url,
      reddit_static_ip,
    }
  }

  fn generate_oxylabs_proxy() -> anyhow::Result<String> {
    let user = env::var("OXYLABS_USER")
      .map_err(|_| anyhow::anyhow!("OXYLABS_USER not set"))?;
    let key = env::var("OXYLABS_KEY")
      .map_err(|_| anyhow::anyhow!("OXYLABS_KEY not set"))?;

    let username = encode(&user);
    let password = encode(&key);

    let session_id: u32 = rand::random_range(100000..999999);

    let full_username = format!("customer-{}-cc-ID-sessid-{}", username, session_id);

    Ok(format!(
      "http://{}:{}@pr.oxylabs.io:7777",
      full_username, password
    ))
  }

  pub fn get_subreddit_url(&self, subreddit: &str) -> String {
    format!("{}/r/{}.json?limit=100", self.base_url, subreddit)
  }

  pub fn get_subreddit_pagination_url(&self, subreddit: &str, after: &str) -> String {
    format!("{}/r/{}.json?limit=100&after={}", self.base_url, subreddit, after)
  }
}
