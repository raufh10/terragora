import json
import psycopg
from psycopg.rows import dict_row
from services.config import configs

def get_db_connection():
  return psycopg.connect(configs.conn_str.get_secret_value(), row_factory=dict_row)

def fetch_relevant_posts(conn, query_embedding: list, limit: int = 5):
  query = """
    SELECT 
      id, 
      title, 
      content, 
      price,
      metadata,
      1 - (embedding <=> %s::vector) AS similarity
    FROM reddit_posts
    WHERE is_active = true
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
  """

  with conn.cursor() as cur:
    cur.execute(query, (query_embedding, query_embedding, limit))
    return cur.fetchall()
