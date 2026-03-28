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

import asyncio
from datetime import datetime
from services.pg import (
  get_db_connection, 
  get_batches, 
  update_batch, 
  bulk_update_post_data,
  fetch_posts_to_process # Assumed helper to get posts by list of IDs
)
from services.llm import client
from services.orchestration import sync_and_process_batches
from services.process import orchestrate_embedding_batch
from services.utils import extract_category, assemble_embedding_text

async def run_data_vectorization():
  conn = get_db_connection()
  try:
    # 1. Sync and Process completed "structured" batches
    # This downloads the price/notes from OpenAI and saves them to batches.data
    await sync_and_process_batches(conn, client, "system_processor", "structured")

    # 2. Fetch "downloaded" structured batches that haven't been applied yet
    downloaded_batches = get_batches(conn, owner="system_processor", batch_type="structured")
    target_batches = [b for b in downloaded_batches if b['status'] == 'downloaded']

    if not target_batches:
      print("😴 No downloaded structured results to vectorize.")
      return

    for batch in target_batches:
      results = batch.get('data', {}).get('results', {})
      if not results:
        continue

      # 3. Match custom_id to extract original post IDs
      # Expected custom_id: f"leaddits-process-{date_str}-{post_id}"
      price_updates = []
      notes_updates = []
      post_ids = []

      for custom_id, data in results.items():
        try:
          original_post_id = custom_id.split("-")[-1]
          post_ids.append(original_post_id)
          
          # Prepare bulk updates
          price_updates.append((data.get('price'), original_post_id))
          notes_updates.append((data.get('notes'), original_post_id))
        except Exception as e:
          print(f"⚠️ Failed to parse ID from {custom_id}: {e}")

      # 4. Save Extracted Data to reddit_posts
      if price_updates:
        bulk_update_post_data(conn, 'price', price_updates)
        bulk_update_post_data(conn, 'notes', notes_updates)

      # 5. Assemble Text for Embedding
      # Fetch the updated posts to get titles and metadata (categories)
      updated_posts = fetch_posts_to_process(conn, post_ids=post_ids)
      embedding_payload = []

      for post in updated_posts:
        category = extract_category(post.get('metadata', {}))
        text_to_embed = assemble_embedding_text(
          title=post['title'],
          price=post['price'],
          notes=post['notes'],
          category=category
        )
        embedding_payload.append({"id": str(post['id']), "text": text_to_embed})

      # 6. Trigger Embedding Batch
      print(f"🚀 Orchestrating embedding batch for {len(embedding_payload)} posts...")
      emb_batch = await orchestrate_embedding_batch(
        owner="system_processor",
        texts=embedding_payload,
        custom_metadata={"parent_batch_id": batch['id']}
      )

      if emb_batch:
        # Mark the structured batch as fully 'processed' so we don't do it again
        update_batch(conn, batch['id'], status="completed")
        print(f"✅ Vectorization batch created: {emb_batch.id}")

  finally:
    conn.close()

import asyncio
from services.pg import (
  get_db_connection, 
  get_batches, 
  update_batch, 
  bulk_update_embeddings
)
from services.llm import client
from services.orchestration import sync_and_process_batches

async def run_data_storage():
  """
  Final stage: Syncs embedding batches, parses vectors, 
  and stores them in the reddit_posts table.
  """
  conn = get_db_connection()
  try:
    # 1. Sync and Process completed "embedding" batches from OpenAI
    # This downloads the vectors and saves them into batches.data['results']
    await sync_and_process_batches(conn, client, "system_processor", "embedding")

    # 2. Fetch 'downloaded' embedding batches that haven't been applied to posts yet
    downloaded_batches = get_batches(conn, owner="system_processor", batch_type="embedding")
    target_batches = [b for b in downloaded_batches if b['status'] == 'downloaded']

    if not target_batches:
      print("😴 No downloaded embedding results to store.")
      return

    for batch in target_batches:
      results = batch.get('data', {}).get('results', {})
      if not results:
        print(f"⚠️ Batch {batch['id']} has no result data. Skipping.")
        continue

      # 3. Match custom_id to extract original post UUIDs
      # Expected custom_id: f"leaddits-embed-{date_str}-{post_id}"
      embedding_updates = []

      for custom_id, vector in results.items():
        try:
          # Extract the UUID (the last part of your custom_id string)
          original_post_id = custom_id.split("-")[-1]
          
          # Prepare tuple for executemany: (vector, post_id)
          embedding_updates.append((vector, original_post_id))
        except Exception as e:
          print(f"⚠️ Failed to parse ID from custom_id '{custom_id}': {e}")

      # 4. Perform Bulk Update to reddit_posts.embedding
      if embedding_updates:
        print(f"💾 Storing {len(embedding_updates)} vectors for batch {batch['id']}...")
        bulk_update_embeddings(conn, embedding_updates)

      # 5. Label Batch as 'completed'
      # This moves it out of the 'downloaded' queue so it won't run again
      update_batch(conn, batch['id'], status="completed")
      print(f"✅ Batch {batch['id']} fully processed and storage complete.")

  finally:
    conn.close()

