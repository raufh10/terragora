import asyncio
import requests
from datetime import datetime, timezone
from services.database import db, submissions

def do_fetch_submissions(logger=None):

  from services.config import settings
  api = getattr(settings, "API_ENDPOINT", None)
  if not api:
    logger.error("❌ Missing settings.API_ENDPOINT")
    return

  url = f"{api.rstrip('/')}/submissions/fetch"
  payload = {
    "subreddit": "dataengineering",
    "limit": 10,
    "sort": "hot",
    "time_filter": "day",
    "fields": ["id", "title", "author", "score", "permalink", "created_utc"],
  }

  try:
    logger.info(f"📡 POST {url}")
    resp = requests.post(url, json=payload, timeout=30)
    if not resp.ok:
      logger.error(f"⚠️ Fetch failed [{resp.status_code}] → {resp.text[:300]}")
      return

    try:
      data = resp.json()
    except ValueError:
      logger.error("⚠️ Response is not valid JSON")
      return

    ok = bool(data.get("ok"))
    counts = data.get("counts") or {}
    results = data.get("results") or []
    settings_echo = data.get("settings") or {}

    if not ok:
      logger.warning(
        f"⚠️ Fetch returned ok=false | counts={counts} results_len={len(results)}"
      )
      return

    logger.info(
      f"✅ Fetch complete | subreddits={counts.get('subreddits')} "
      f"submissions={counts.get('submissions')} results_len={len(results)} "
      f"sort={settings_echo.get('sort')} time_filter={settings_echo.get('time_filter')} "
      f"limit={settings_echo.get('limit')} fields={settings_echo.get('fields')}"
    )

    to_insert_data = []
    for subreddit, posts in results.items():
      if not isinstance(posts, list):
        continue
      for post in posts:
        if isinstance(post, dict):
          to_insert_data.append({
            "subreddit": subreddit,
            "data": post
          })

    supabase = db.get_supabase_client()
    try:
      status = asyncio.run(submissions.insert(supabase, logger, to_insert_data))
    except Exception as e:
      logger.error(f"❌ Insert exception: {e}")

    if status:
      logger.info("📥 Insert is complete")

  except requests.RequestException as e:
    logger.exception(f"❌ Request error calling {url}: {e}")