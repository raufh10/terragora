import json
import asyncio
from typing import List
from services.llm import extract_product_details, get_embedding
from services.utils import clean_text, extract_category, assemble_embedding_text

from services.pg import (
  fetch_posts_to_process, 
  bulk_update_post_data, 
  bulk_update_embeddings
)

async def run_data_extraction(conn):

  posts = fetch_posts_to_process(conn, batch_type="extraction", limit=20)
  if not posts:
    print("😴 No new posts needing extraction.")
    return

  print(f"🧐 Processing {len(posts)} posts for extraction...")
  
  price_updates = []
  notes_updates = []
  
  semaphore = asyncio.Semaphore(5)

  async def process_single_post(post):
    async with semaphore:
      post_id = post['id']
      full_text = clean_text(f"{post.get('title', '')} {post.get('content', '')}")
      
      extracted = await extract_product_details(full_text)
      if extracted:
        price_data = [p.model_dump() for p in extracted.prices]
        
        from psycopg.types.json import Jsonb
        price_updates.append((Jsonb(price_data), post_id))
        notes_updates.append((extracted.notes, post_id))
        print(f"✅ Extracted: {post['title'][:40]}...")

  await asyncio.gather(*(process_single_post(p) for p in posts))

  if price_updates:
    bulk_update_post_data(conn, 'price', price_updates)
    bulk_update_post_data(conn, 'notes', notes_updates)
    print(f"✨ Extraction complete: {len(price_updates)} items updated.")

async def run_data_vectorization(conn):

  posts = fetch_posts_to_process(conn, batch_type="vectorization", limit=50)
  if not posts:
    print("😴 No posts ready for vectorization.")
    return

  print(f"🚀 Generating embeddings for {len(posts)} posts...")
  embedding_updates = []
  semaphore = asyncio.Semaphore(10)

  async def vectorize_single_post(post):
    async with semaphore:
      category = extract_category(post.get('metadata', {}))
      
      rich_text = assemble_embedding_text(
        title=post['title'],
        price=post.get('price'), # This is the JSON list from DB
        notes=post.get('notes', ''),
        category=category
      )
      
      vector = await get_embedding(rich_text)
      if vector:
        embedding_updates.append((vector, post['id']))

  await asyncio.gather(*(vectorize_single_post(p) for p in posts))

  if embedding_updates:
    bulk_update_embeddings(conn, embedding_updates)
    print(f"✨ Storage complete: {len(embedding_updates)} vectors generated.")
