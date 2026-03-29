import asyncio
import json
from typing import Optional, Dict, Any, List
from openai import OpenAI
from services.config import configs
from services.models import ProductExtraction
from services.utils import clean_text, extract_category, assemble_embedding_text
from services.jsonl import extract_batch_embeddings, process_batch_output
from services.llm import retrieve_batch_status, get_file_content
from services.process import orchestrate_structured_batch, orchestrate_embedding_batch
from services.pg import (
  get_batches, 
  update_batch, 
  bulk_update_post_data, 
  bulk_update_embeddings, 
  fetch_posts_to_process
)

async def sync_and_process_batches(conn, client: OpenAI, owner: str, batch_type: str):
  """
  Checks pending batches in DB, syncs status with OpenAI, and parses results.
  """
  batches = get_batches(conn, owner=owner, batch_type=batch_type)
  active_statuses = ['completed', 'failed', 'expired', 'cancelled', 'downloaded', 'saved']
  active_batches = [b for b in batches if b['status'] not in active_statuses]

  if not active_batches:
    print(f"ℹ️ No active {batch_type} batches to sync.")
    return

  for db_batch in active_batches:
    batch_id = db_batch['id']
    remote_batch = await retrieve_batch_status(client, batch_id)
    if not remote_batch:
      continue

    if remote_batch.status == "completed":
      file_id = remote_batch.output_file_id
      if not file_id:
        update_batch(conn, batch_id, status="failed")
        continue

      file_response = await get_file_content(client, file_id)
      if file_response:
        raw_content = file_response.text
        results = extract_batch_embeddings(raw_content) if batch_type == "embedding" else process_batch_output(raw_content)
        
        update_batch(conn, batch_id, status="downloaded", result={"results": results})
        print(f"✅ Batch {batch_id} downloaded: {len(results)} items.")

    elif remote_batch.status in ["failed", "expired", "cancelled"]:
      update_batch(conn, batch_id, status="failed")
    elif remote_batch.status != db_batch['status']:
      update_batch(conn, batch_id, status=remote_batch.status)

async def run_data_extraction(conn, client: OpenAI):
  """
  Stage 1: Fetch raw posts and create a structured extraction batch.
  """
  posts = fetch_posts_to_process(conn)
  if not posts:
    print("😴 No new posts to process.")
    return

  texts_to_process = []
  post_ids = []

  for post in posts:
    post_id = str(post['id'])
    cleaned = clean_text(f"{post['title']} {post['content']}")
    texts_to_process.append({"id": post_id, "text": cleaned})
    post_ids.append(post_id)

  batch_job = await orchestrate_structured_batch(
    conn=conn,
    client=client,
    owner="system_processor",
    texts=texts_to_process,
    model_class=ProductExtraction,
    schema_name="marketplace_extraction_v1",
    system_prompt=configs.ProductExtractionPrompt,
    custom_metadata={"post_ids": post_ids, "source": "reddit_marketplace"}
  )

  if batch_job:
    print(f"🚀 Extraction Batch Created: {batch_job.id}")

async def run_data_vectorization(conn, client: OpenAI):
  """
  Stage 2: Apply extracted prices/notes and create an embedding batch.
  """
  await sync_and_process_batches(conn, client, "system_processor", "structured")

  downloaded_batches = get_batches(conn, owner="system_processor", batch_type="structured")
  target_batches = [b for b in downloaded_batches if b['status'] == 'downloaded']

  for batch in target_batches:
    results = batch.get('result', {}).get('results', {})
    if not results: continue

    price_updates, notes_updates, post_ids = [], [], []

    for custom_id, data in results.items():
      original_post_id = custom_id.split("-")[-1]
      post_ids.append(original_post_id)
      price_updates.append((data.get('prices'), original_post_id))
      notes_updates.append((data.get('notes'), original_post_id))

    bulk_update_post_data(conn, 'price', price_updates)
    bulk_update_post_data(conn, 'notes', notes_updates)
    update_batch(conn, batch_id.get('id'), status="saved")

    updated_posts = fetch_posts_to_process(conn, post_ids=post_ids)
    embedding_payload = []

    for post in updated_posts:
      category = extract_category(post.get('metadata', {}))
      text_to_embed = assemble_embedding_text(
        title=post['title'], price=post['price'], notes=post['notes'], category=category
      )
      embedding_payload.append({"id": str(post['id']), "text": text_to_embed})

    emb_batch = await orchestrate_embedding_batch(
      conn=conn, client=client, owner="system_processor",
      texts=embedding_payload, custom_metadata={"parent_batch_id": batch['id']}
    )

    if emb_batch:
      print(f"✅ Vectorization batch created: {emb_batch.id}")

async def run_data_storage(conn, client: OpenAI):
  """
  Stage 3: Download embeddings and store them in the database.
  """
  await sync_and_process_batches(conn, client, "system_processor", "embedding")

  downloaded_batches = get_batches(conn, owner="system_processor", batch_type="embedding")
  target_batches = [b for b in downloaded_batches if b['status'] == 'downloaded']

  for batch in target_batches:
    results = batch.get('data', {}).get('results', {})
    if not results: continue

    embedding_updates = []
    for custom_id, vector in results.items():
      original_post_id = custom_id.split("-")[-1]
      embedding_updates.append((vector, original_post_id))

    if embedding_updates:
      bulk_update_embeddings(conn, embedding_updates)

    update_batch(conn, batch.get("id"), status="saved")
    print(f"✅ Storage complete for batch: {batch['id']}")
