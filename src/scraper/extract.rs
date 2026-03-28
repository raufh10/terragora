use crate::models::{RedditResponse, RedditUrlResponse};
use serde_json::Value;

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

pub fn process_url_response(response: RedditUrlResponse) -> Vec<RawScrapedPost> {
  // Reddit URL responses are Vec<RedditResponse>. 
  // Index 0 is the Post listing, Index 1 is the Comments listing.
  if let Some(post_listing) = response.0.into_iter().next() {
    return process_response(post_listing);
  }
  
  Vec::new()
}

pub fn process_response(response: RedditResponse) -> Vec<RawScrapedPost> {
  response.data.children
    .into_iter()
    .filter(|child| {
      // Logic: Only posts with flairs
      match &child.data.link_flair_richtext {
        Some(flair) => !flair.is_empty(),
        None => false,
      }
    })
    .map(|child| {
      let post = child.data;
      // Capture the full data for the metadata column
      let raw_val = serde_json::to_value(&post).unwrap_or(Value::Null);
      
      RawScrapedPost {
        reddit_id: post.reddit_id,
        title: post.title,
        selftext: post.selftext,
        url: post.url,
        created_utc: post.created_utc,
        subreddit: post.subreddit,
        raw_json: raw_val,
      }
    })
    .collect()
}

pub fn process_response_to_storable(raw_posts: Vec<RawScrapedPost>) -> Vec<StorablePost> {
  raw_posts.into_iter().map(|post| {
    StorablePost {
      reddit_id: post.reddit_id,
      title: post.title,
      content: post.selftext,
      url: post.url,
      created_at: post.created_utc,
      raw_json: post.raw_json,
    }
  }).collect()
}
