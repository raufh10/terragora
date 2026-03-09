use sqlx::{Pool, Postgres};
use crate::scraper::extract::StorablePost;
use chrono::{Utc, TimeZone};

pub async fn bulk_ingest_raw_posts(
  pool: &Pool<Postgres>,
  posts: &[StorablePost],
) -> Result<(), sqlx::Error> {
  let reddit_ids: Vec<String> = posts.iter().map(|p| p.reddit_id.clone()).collect();
  let titles: Vec<String> = posts.iter().map(|p| p.title.clone()).collect();
  let contents: Vec<String> = posts.iter().map(|p| p.content.clone()).collect();
  let urls: Vec<String> = posts.iter().map(|p| p.url.clone()).collect();
  let metadata_json: Vec<serde_json::Value> = posts.iter().map(|p| p.raw_json.clone()).collect();
  
  let posted_at: Vec<chrono::DateTime<Utc>> = posts
    .iter()
    .map(|p| Utc.timestamp_opt(p.created_at as i64, 0).unwrap())
    .collect();

  sqlx::query!(
    r#"
    INSERT INTO reddit_posts (reddit_id, title, content, url, posted_at, metadata, embedding)
    SELECT * FROM UNNEST(
      $1::text[], 
      $2::text[], 
      $3::text[], 
      $4::text[], 
      $5::timestamptz[], 
      $6::jsonb[],
      CAST(NULL AS vector[]) -- Placeholder for Python to fill
    )
    ON CONFLICT (reddit_id) DO UPDATE SET
      title = EXCLUDED.title,
      content = EXCLUDED.content,
      metadata = EXCLUDED.metadata,
      scraped_at = NOW()
    "#,
    &reddit_ids,
    &titles,
    &contents,
    &urls,
    &posted_at,
    &metadata_json
  )
  .execute(pool)
  .await?;

  Ok(())
}

