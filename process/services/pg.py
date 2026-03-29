import json
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from services.config import configs

def get_db_connection():
  active_str = configs.active_conn_str

  try:
    return psycopg.connect(
      active_str.get_secret_value(), 
      row_factory=dict_row
    )
  except Exception as e:
    print(f"[ERROR] Failed to connect to {configs.env} database: {e}")
    raise

def fetch_posts_to_process(conn, batch_type: str = "extraction", limit: int = 200):

  if batch_type == "extraction":
    query = """
      SELECT id, title, content, metadata 
      FROM reddit_posts 
      WHERE is_active = true 
      AND (notes IS NULL OR price IS NULL OR price = '[]'::jsonb)
      LIMIT %s
    """

  elif batch_type == "vectorization":
    query = """
      SELECT id, title, price, notes, metadata 
      FROM reddit_posts 
      WHERE is_active = true 
      AND notes IS NOT NULL 
      AND embedding IS NULL
      LIMIT %s
    """

  else:
    raise ValueError(f"Unknown batch_type: {batch_type}")

  with conn.cursor() as cur:
    cur.execute(query, (limit,))
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

def bulk_update_post_data(conn, column_name, updates):

  query = f"UPDATE reddit_posts SET {column_name} = %s WHERE id = %s"
  try:
    with conn.cursor() as cur:
      cur.executemany(query, updates)
    conn.commit()
    print(f"✅ Successfully updated {len(updates)} records in '{column_name}'.")
  except Exception as e:
    conn.rollback()
    print(f"❌ Bulk {column_name} update failed: {e}")

def deactivate_old_posts(conn):

  query = """
    UPDATE reddit_posts
    SET is_active = FALSE
    WHERE posted_at < NOW() - INTERVAL '1 month'
    AND is_active = TRUE
  """

  try:
    with conn.cursor() as cur:
      cur.execute(query)
      affected = cur.rowcount
    conn.commit()
    print(f"✅ Deactivated {affected} posts older than 1 month.")
  except Exception as e:
    conn.rollback()
    print(f"❌ Failed to deactivate old posts: {e}")
