from sys import exit

import asyncio
from services.pg import (
  get_db_connection,
  fetch_posts_to_process,
  bulk_update_embeddings,
  bulk_update_prices
)
from services.process import extract_product_details, get_embedding
from services.utils import clean_text, assemble_embedding_text, format_payloads, extract_category

async def run_processor():
  conn = get_db_connection()
  try:
    posts = fetch_posts_to_process(conn)
    if not posts:
      print("😴 No new posts to process.")
      return

    print(f"🧐 Found {len(posts)} posts to process.")
    processed_results = []

    for post in posts:
      raw_content = f"{post['title']} {post['content']}"
      cleaned = clean_text(raw_content)

      category = extract_category(post.get('metadata', {}))
      product_info = await extract_product_details(cleaned)
      
      if product_info:
        primary_price = product_info.prices[0] if product_info.prices else None        

        embedding_text = assemble_embedding_text(
          post['title'], 
          primary_price, 
          product_info.notes, 
          category
        )

        vector = await get_embedding(embedding_text)
        
        processed_results.append({
          'id': post['id'],
          'price': primary_price,
          'embedding': vector
        })
        print(f"✨ Processed: {post['title'][:30]}...")

    price_data, embedding_data = format_payloads(processed_results)    
    if price_data:
      bulk_update_prices(conn, price_data)
    if embedding_data:
      bulk_update_embeddings(conn, embedding_data)

  finally:
    conn.close()

if __name__ == "__main__":
  asyncio.run(run_processor())
