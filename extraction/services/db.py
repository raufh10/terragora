from services.config import configs
from supabase import create_client, Client
from typing import Optional

def get_supabase_client() -> Client:
  return create_client(
    configs.supabase_url.get_secret_value(),
    configs.supabase_key.get_secret_value()
  )

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
