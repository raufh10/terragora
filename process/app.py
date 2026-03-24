import asyncio
from typing import List
from services.pg import (
  get_db_connection,
  fetch_posts_to_process,
  insert_batch
)
from services.process import orchestrate_structured_batch
from services.models import ProductExtraction
from services.utils import clean_text

async def run_batch_processor():
  conn = get_db_connection()
  try:
    posts = fetch_posts_to_process(conn)
    if not posts:
      print("😴 No new posts to process.")
      return

    print(f"🧐 Found {len(posts)} posts for batch processing.")
    
    texts_to_process = []
    post_ids = []
    
    for post in posts:
      raw_content = f"{post['title']} {post['content']}"
      cleaned = clean_text(raw_content)
      texts_to_process.append(cleaned)
      post_ids.append(post['id'])

    batch_job = await orchestrate_structured_batch(
      owner="system_processor",
      texts=texts_to_process,
      model_class=ProductExtraction,
      schema_name="marketplace_extraction_v1",
      system_prompt="Extract pricing and 1-3 sentences of seller notes from the marketplace post with high precision.",
      custom_metadata={
        "post_ids": post_ids,
        "source": "reddit_marketplace"
      }
    )

    if batch_job:
      print(f"🚀 Batch Job Created!")
      print(f"🆔 ID: {batch_job.id}")
      print(f"📊 Status: {batch_job.status}")
      print(f"📝 Tracking post IDs: {len(post_ids)} items submitted.")
    else:
      print("❌ Failed to create batch job.")

  finally:
    conn.close()

if __name__ == "__main__":
  asyncio.run(run_batch_processor())
