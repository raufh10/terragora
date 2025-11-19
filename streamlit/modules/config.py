import os

PAGE_SIZE = 10
TYPE_OPTIONS = [
  "stats",
  "insights",
  "highlights",
  "tickets_related",
  "interaction",
  "praises",
  "critics",
  "meme",
  "player_stats",
  "lineups",
  "trade",
  "free_agency",
  "performance",
  "chemistry",
  "g_league",
  "podcast",
  "press_conference",
  "sports_panel",
  "other_teams",
  "throwback",
  "misc_talk",
]
LOCATION_OPTIONS = ["global", "US"]

def get_backend_api_endpoint():
  #endpoint = os.getenv("BACKEND_API_ENDPOINT", "http://127.0.0.1:8000/")
  endpoint = os.getenv("BACKEND_API_ENDPOINT", "http://leaddits_api.railway.internal:8080")

  if not endpoint:
    raise EnvironmentError("Missing required environment variable: API_ENDPOINT")
  return endpoint

def get_supabase_url():
  endpoint = os.getenv("SUPABASE_URL", "https://bmcyccxnavcnhaositeh.supabase.co")

  if not endpoint:
    raise EnvironmentError("Missing required environment variable: SUPABASE_URL")
  return endpoint

def get_supabase_public_key():
  endpoint = os.getenv("SUPABASE_PUBLIC_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtY3ljY3huYXZjbmhhb3NpdGVoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk4MTAwMjksImV4cCI6MjA2NTM4NjAyOX0.knB-Dj0QeQkCuQ_CJMHaIVo863A7huSezfMZvAInpJs")

  if not endpoint:
    raise EnvironmentError("Missing required environment variable: SUPABASE_KEY")
  return endpoint
