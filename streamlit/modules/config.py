import os

def get_backend_api_endpoint():
  endpoint = os.getenv("BACKEND_API_ENDPOINT", "http://127.0.0.1:8000")

  if not endpoint:
    raise EnvironmentError("Missing required environment variable: API_ENDPOINT")
  return endpoint

def get_supabase_url():
  endpoint = os.getenv("SUPABASE_URL")

  if not endpoint:
    raise EnvironmentError("Missing required environment variable: SUPABASE_URL")
  return endpoint

def get_supabase_public_key():
  endpoint = os.getenv("SUPABASE_KEY")

  if not endpoint:
    raise EnvironmentError("Missing required environment variable: SUPABASE_KEY")
  return endpoint
