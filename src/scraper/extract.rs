use crate::models::{RedditResponse, StorablePost};
use serde_json::Value;

pub fn process_response(response: RedditResponse) -> Vec<StorablePost> {
  response.data.children
    .into_iter()
    .map(|child| {
      let post = child.data;

      let has_wts = post.link_flair_richtext
        .as_ref()
        .map(|flairs| {
          flairs.iter().any(|f| {
            f.get("t")
              .and_then(|t| t.as_str())
              .map(|text| text.to_ascii_uppercase().contains("WTS"))
              .unwrap_or(false)
          })
        })
        .unwrap_or(false);

      let raw_json = serde_json::to_value(&post).unwrap_or(Value::Null);

      StorablePost {
        reddit_id: post.reddit_id,
        title: post.title,
        content: post.selftext,
        url: post.url,
        posted_at: post.created_utc,
        metadata: raw_json,
        is_active: has_wts,
      }
    })
    .collect()
}
