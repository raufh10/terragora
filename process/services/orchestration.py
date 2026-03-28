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

async def run_data_extraction():
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
      post_id = str(post['id'])
      raw_content = f"{post['title']} {post['content']}"
      cleaned = clean_text(raw_content)

      text_dict = {"id": post_id, "text": cleaned}
      texts_to_process.append(text_dict)
      post_ids.append(post_id)

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

import json
from typing import Optional, Dict, Any
from openai import OpenAI
from services.pg import get_batches, update_batch
from services.llm import retrieve_batch_status, get_file_content
from services.jsonl import extract_batch_embeddings, process_batch_output

async def sync_and_process_batches(conn, client: OpenAI, owner: str, batch_type: str):
  """
  Checks pending batches in DB, syncs status with OpenAI, 
  and parses results if completed.
  """
  # 1. Filter out batches that are already finished or have been downloaded
  batches = get_batches(conn, owner=owner, batch_type=batch_type)
  
  active_batches = [
    b for b in batches 
    if b['status'] not in ['completed', 'failed', 'expired', 'cancelled', 'downloaded']
  ]
  
  if not active_batches:
    print(f"ℹ️ No active {batch_type} batches to sync for {owner}.")
    return

  for db_batch in active_batches:
    batch_id = db_batch['id']
    print(f"🔄 Syncing {batch_type} batch: {batch_id}...")

    # 2. Retrieve fresh status from OpenAI
    remote_batch = await retrieve_batch_status(client, batch_id)
    if not remote_batch:
      continue

    # 3. Handle Completion
    if remote_batch.status == "completed":
      file_id = remote_batch.output_file_id
      
      if not file_id:
        print(f"⚠️ Batch {batch_id} marked completed but no output_file_id found.")
        update_batch(conn, batch_id, status="failed")
        continue

      # Download and Parse content
      file_response = await get_file_content(client, file_id)
      if file_response:
        raw_content = file_response.text
        
        # Determine parser based on type
        results = {}
        if batch_type == "embedding":
          results = extract_batch_embeddings(raw_content)
        elif batch_type == "structured":
          results = process_batch_output(raw_content)

        # Update DB with status 'downloaded' and the parsed data
        update_batch(conn, batch_id, status="downloaded", data={"results": results})
        print(f"✅ Batch {batch_id} processed: {len(results)} items extracted.")

    # 4. Handle Errors/Failures
    elif remote_batch.status in ["failed", "expired", "cancelled"]:
      print(f"❌ Batch {batch_id} failed with status: {remote_batch.status}")
      update_batch(conn, batch_id, status="failed")

    # 5. Still Processing
    else:
      print(f"⏳ Batch {batch_id} is still {remote_batch.status}...")
      if remote_batch.status != db_batch['status']:
        update_batch(conn, batch_id, status=remote_batch.status)
