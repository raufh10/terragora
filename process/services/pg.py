import json
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
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

def fetch_posts_to_process(conn):
  query = """
    SELECT id, title, content, metadata
    FROM reddit_posts
    WHERE embedding IS NULL 
    AND is_active = true
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

def insert_batch(conn, batch_id: str, file_input_id: str, owner: str, data: Dict[str, Any], type: str, status: str = "validating"):
  query = """
    INSERT INTO batches (id, file_input_id, owner, data, type, status)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING *;
  """
  with conn.cursor() as cur:
    cur.execute(query, (batch_id, file_input_id, owner, Jsonb(data), type, status))
    conn.commit()
    return cur.fetchone()

def update_batch(conn, batch_id: str, status: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
  updates = []
  params = []

  if status:
    updates.append("status = %s")
    params.append(status)
  if data:
    updates.append("data = %s")
    params.append(Jsonb(data))

  if not updates:
    return None

  params.append(batch_id)
  query = f"UPDATE batches SET {', '.join(updates)} WHERE id = %s RETURNING *;"

  with conn.cursor() as cur:
    cur.execute(query, params)
    conn.commit()
    return cur.fetchone()

def get_batches(
  conn, 
  owner: Optional[str] = None, 
  batch_id: Optional[str] = None, 
  batch_type: Optional[str] = None
) -> List[Dict]:
  if batch_id:
    query = "SELECT * FROM batches WHERE id = %s;"
    params = (batch_id,)
  elif owner:
    if batch_type:
      query = "SELECT * FROM batches WHERE owner = %s AND type = %s ORDER BY created_at DESC;"
      params = (owner, batch_type)
    else:
      query = "SELECT * FROM batches WHERE owner = %s ORDER BY created_at DESC;"
      params = (owner,)
  elif batch_type:
    query = "SELECT * FROM batches WHERE type = %s ORDER BY created_at DESC LIMIT 100;"
    params = (batch_type,)
  else:
    query = "SELECT * FROM batches ORDER BY created_at DESC LIMIT 100;"
    params = ()

  with conn.cursor() as cur:
    cur.execute(query, params)
    return cur.fetchall()
