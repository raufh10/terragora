use sqlx::{Pool, Postgres};
use crate::scraper::extract::StorablePost;
use crate::models::{RedditUrlStatuses, RedditUrls};
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

pub async fn fetch_active_reddit_urls(pool: &Pool<Postgres>) -> Result<RedditUrls, sqlx::Error> {
  let rows = sqlx::query!(
    r#"
    SELECT url 
    FROM reddit_posts 
    WHERE is_active = true
    "#
  )
  .fetch_all(pool)
  .await?;

  let urls = rows.into_iter().map(|r| r.url.unwrap_or_default()).collect();
  
  Ok(RedditUrls { urls })
}

pub async fn bulk_update_url_statuses(
  pool: &Pool<Postgres>,
  statuses: &RedditUrlStatuses,
) -> Result<(), sqlx::Error> {
  let urls: Vec<String> = statuses.items.iter().map(|i| i.url.clone()).collect();
  let activity_flags: Vec<bool> = statuses.items.iter().map(|i| i.is_active).collect();

  sqlx::query!(
    r#"
    UPDATE reddit_posts AS rp
    SET is_active = data.new_status
    FROM (
      SELECT * FROM UNNEST($1::text[], $2::boolean[])
    ) AS data(url, new_status)
    WHERE rp.url = data.url
    "#,
    &urls,
    &activity_flags
  )
  .execute(pool)
  .await?;

  Ok(())
}
