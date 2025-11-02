from services.config import credentials
from supabase import create_client, Client

def get_supabase_client() -> Client:
  return create_client(
    credentials.supabase_url.get_secret_value(),
    credentials.supabase_key.get_secret_value()
  )
