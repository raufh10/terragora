use crate::models::{RedditResponse, RawScrapedPost, StorablePost};
use serde_json::Value;

/// Processes a standard Reddit API response, filtering for "WTS" flairs.
pub fn process_response(response: RedditResponse) -> Vec<RawScrapedPost> {
  response.data.children
    .into_iter()
    .filter(|child| {
      // Extract flairs safely; if none exist or it's empty, discard the post.
      let flairs = match &child.data.link_flair_richtext {
        Some(f) if !f.is_empty() => f,
        _ => return false,
      };

      // Only keep posts where at least one flair contains "WTS" (case-insensitive)
      flairs.iter().any(|f| {
        f.get("t")
          .and_then(|t| t.as_str())
          .map(|text| text.to_ascii_uppercase().contains("WTS"))
          .unwrap_or(false)
      })
    })
    .map(|child| {
      let post = child.data;
      // Convert the post back to raw JSON for the raw_json field
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

/// Maps the scraped posts into a flatter format suitable for database storage.
pub fn process_response_to_storable(raw_posts: Vec<RawScrapedPost>) -> Vec<StorablePost> {
  raw_posts
    .into_iter()
    .map(|post| {
      StorablePost {
        reddit_id: post.reddit_id,
        title: post.title,
        content: post.selftext,
        url: post.url,
        created_at: post.created_utc,
        raw_json: post.raw_json,
      }
    })
    .collect()
}

