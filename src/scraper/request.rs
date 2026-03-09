use reqwest::header::{HeaderMap, HeaderValue, USER_AGENT};
use crate::models::RedditResponse;
use std::net::SocketAddr;
use std::time::Duration;

pub async fn init_client(timeout: u64) -> Result<reqwest::Client, Box<dyn std::error::Error>> {
    // The "Magic" Fastly IP to bypass Internet Positif DNS injection
    let reddit_ip: SocketAddr = "151.101.129.140:443".parse()?;

    let client = reqwest::Client::builder()
        // Layer 1 & 2: Manual IP Resolve (DNS Bypass)
        .resolve("www.reddit.com", reddit_ip)
        .resolve("reddit.com", reddit_ip)
        // Layer 3: Independent Encryption (Handshake Bypass)
        .use_rustls_tls() 
        .timeout(Duration::from_secs(timeout))
        .build()?;
    
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

