import asyncio
from typing import List
from openai import OpenAI
from services.llm import extract_product_details, get_embedding
from services.utils import clean_text, extract_category, assemble_embedding_text
from services.pg import (
  fetch_posts_to_process, 
  bulk_update_post_data, 
  bulk_update_embeddings
)

async def run_data_extraction(conn):
  """
  Stage 1: Real-time extraction. 
  Uses GPT-5.4 Nano to parse prices and notes immediately.
  """
  posts = fetch_posts_to_process(conn)
  if not posts:
    print("😴 No new posts needing extraction.")
    return

  print(f"🧐 Processing {len(posts)} posts for extraction...")
  
  price_updates = []
  notes_updates = []

  # We use a semaphore to avoid hitting OpenAI rate limits during real-time calls
  semaphore = asyncio.Semaphore(5) 

  async def process_single_post(post):
    async with semaphore:
      post_id = post['id']
      text = clean_text(f"{post['title']} {post['content']}")
      
      extracted = await extract_product_details(text)
      if extracted:
        # Note: extracted.prices is now a list of objects per your new model
        price_updates.append((json.dumps([p.model_dump() for p in extracted.prices]), post_id))
        notes_updates.append((extracted.notes, post_id))
        print(f"✅ Extracted: {post['title'][:30]}...")

  # Run extractions in parallel
  await asyncio.gather(*(process_single_post(p) for p in posts))

  if price_updates:
    # We store the structured price list in the 'metadata' or 'notes' column, 
    # or you can use a single numeric price if you prefer.
    bulk_update_post_data(conn, 'notes', notes_updates)
    # If your 'price' column is numeric, you may need a helper to pick the first 'start' price.
    print(f"✨ Extraction sync complete for {len(price_updates)} posts.")

async def run_data_vectorization(conn):
  """
  Stage 2: Real-time vectorization.
  Assembles the final searchable string and generates the embedding.
  """
  # Fetch posts that have been extracted (notes exist) but have no embedding
  posts = fetch_posts_to_process(conn) 
  if not posts:
    print("😴 No posts ready for vectorization.")
    return

  print(f"🚀 Generating embeddings for {len(posts)} posts...")
  embedding_updates = []
  semaphore = asyncio.Semaphore(10)

  async def vectorize_single_post(post):
    async with semaphore:
      category = extract_category(post.get('metadata', {}))
      
      # We use the newly extracted notes and prices to build the context
      rich_text = assemble_embedding_text(
        title=post['title'],
        price=None, # Adjust if you want to pull from the new prices list
        notes=post.get('notes', ''),
        category=category
      )
      
      vector = await get_embedding(rich_text)
      if vector:
        embedding_updates.append((vector, post['id']))

  await asyncio.gather(*(vectorize_single_post(p) for p in posts))

  if embedding_updates:
    bulk_update_embeddings(conn, embedding_updates)
    print(f"✨ Storage complete for {len(embedding_updates)} vectors.")

