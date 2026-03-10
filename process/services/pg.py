import json
import psycopg
from psycopg.rows import dict_row
from services.config import configs

def get_db_connection():
  return psycopg.connect(configs.conn_str.get_secret_value(), row_factory=dict_row)

def fetch_posts_to_process(conn):
  query = """
    SELECT id, title, content, metadata
    FROM reddit_posts
    WHERE embedding IS NULL
  """
  with conn.cursor() as cur:
    cur.execute(query)
    return cur.fetchall()

def bulk_update_embeddings(conn, updates):
  query = "UPDATE reddit_posts SET embedding = %s::vector WHERE id = %s"
  try:
    with conn.cursor() as cur:
      cur.executemany(query, updates)
    conn.commit()
    print(f"✅ Successfully updated {len(updates)} embeddings.")
  except Exception as e:
    conn.rollback()
    print(f"❌ Bulk embedding update failed: {e}")

def bulk_update_prices(conn, price_updates):
  query = "UPDATE reddit_posts SET price = %s WHERE id = %s"
  try:
    with conn.cursor() as cur:
      cur.executemany(query, price_updates)
    conn.commit()
    print(f"✅ Successfully updated {len(price_updates)} prices.")
  except Exception as e:
    conn.rollback()
    print(f"❌ Bulk price update failed: {e}")

def update_post_embedding(conn, post_id, embedding):
  query = "UPDATE reddit_posts SET embedding = %s::vector WHERE id = %s"
  try:
    with conn.cursor() as cur:
      cur.execute(query, (embedding, post_id))
    conn.commit()
  except Exception as e:
    conn.rollback()
    print(f"❌ Error updating embedding for post {post_id}: {e}")

def update_post_price(conn, post_id, price):
  query = "UPDATE reddit_posts SET price = %s WHERE id = %s"
  try:
    with conn.cursor() as cur:
      cur.execute(query, (price, post_id))
    conn.commit()
  except Exception as e:
    conn.rollback()
    print(f"❌ Error updating price for post {post_id}: {e}")

