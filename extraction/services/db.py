import psycopg
from pgvector.psycopg import register_vector
from supabase import create_client, Client
from services.config import configs
from typing import List, Dict, Any

def get_supabase_client() -> Client:
  return create_client(
    configs.supabase_url.get_secret_value(),
    configs.supabase_key.get_secret_value()
  )

def get_psycopg_client():
  conn = psycopg.connect(configs.database_url.get_secret_value())
  register_vector(conn)
  return conn

async def insert(
  supabase: Client,
  data: list,
):
  try:
    response = (
      supabase
      .table(f"submissions")
      .upsert(
        data,
        on_conflict="reddit_id"
      )
      .execute()
    )

    if response.data:
      return True

  except Exception as e:
    print(f"Exception bulk insert submissions: {e}")
    return False

async def insert_vectors(data: List[Dict[str, Any]]):

  try:
    with get_psycopg_client() as conn:
      with conn.cursor() as cur:

        for item in data:
          cur.execute(
            """
            INSERT INTO submissions (reddit_id, embedding) 
            VALUES (%s, %s) 
            ON CONFLICT (reddit_id) 
            DO UPDATE SET embedding = EXCLUDED.embedding
            """,
            (item["reddit_id"], item["embedding"])
          )

      conn.commit()
    return True

  except Exception as e:
    print(f"Vector Insert Error: {e}")
    return False

