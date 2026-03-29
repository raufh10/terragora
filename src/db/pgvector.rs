use sqlx::{Pool, Postgres};
use crate::models::StorablePost;
use chrono::{Utc, TimeZone};

pub async fn bulk_ingest_raw_posts(
  pool: &Pool<Postgres>,
  posts: &[StorablePost],
) -> Result<(), sqlx::Error> {
  let reddit_ids: Vec<String> = posts.iter().map(|p| p.reddit_id.clone()).collect();
  let titles: Vec<String> = posts.iter().map(|p| p.title.clone()).collect();
  let contents: Vec<String> = posts.iter().map(|p| p.content.clone()).collect();
  let urls: Vec<String> = posts.iter().map(|p| p.url.clone()).collect();
  let metadata: Vec<serde_json::Value> = posts.iter().map(|p| p.metadata.clone()).collect();
  let is_active: Vec<bool> = posts.iter().map(|p| p.is_active).collect();

  // Convert f64 UTC timestamp to Chrono DateTime
  let posted_at: Vec<chrono::DateTime<Utc>> = posts
    .iter()
    .map(|p| Utc.timestamp_opt(p.posted_at as i64, 0).single().unwrap_or_else(Utc::now))
    .collect();

  sqlx::query!(
    r#"
    INSERT INTO reddit_posts (reddit_id, title, content, url, posted_at, metadata, is_active)
    SELECT * FROM UNNEST(
      $1::text[], 
      $2::text[], 
      $3::text[], 
      $4::text[], 
      $5::timestamptz[], 
      $6::jsonb[],
      $7::boolean[]
    )
    ON CONFLICT (reddit_id) DO UPDATE SET
      title = EXCLUDED.title,
      content = EXCLUDED.content,
      metadata = EXCLUDED.metadata,
      is_active = EXCLUDED.is_active,
      scraped_at = NOW()
    "#,
    &reddit_ids,
    &titles,
    &contents,
    &urls,
    &posted_at,
    &metadata,
    &is_active
  )
  .execute(pool)
  .await?;

  Ok(())
}
