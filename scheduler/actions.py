import requests

def do_fetch_submissions(logger=None):
  """
  POST to /submissions/fetch and log the summary from the JSON response.
  Lazily imports settings to avoid circular import with services.config.settings.
  """
  # Lazy import avoids circular import during module initialization
  from services.config import settings

  api = getattr(settings, "API_ENDPOINT", None)
  if not api:
    logger and logger.error("❌ Missing settings.API_ENDPOINT")
    return

  url = f"{api.rstrip('/')}/submissions/fetch"
  payload = {
    "subreddit": "dataengineering",
    "limit": 25,
    "sort": "hot",
    "time_filter": "day",
    "fields": ["id", "title", "author", "score", "permalink", "created_utc"],
  }

  try:
    logger and logger.info(f"📡 POST {url}")
    resp = requests.post(url, json=payload, timeout=30)
    if not resp.ok:
      logger and logger.error(f"⚠️ Fetch failed [{resp.status_code}] → {resp.text[:300]}")
      return

    try:
      data = resp.json()
    except ValueError:
      logger and logger.error("⚠️ Response is not valid JSON")
      return

    ok = bool(data.get("ok"))
    counts = data.get("counts") or {}
    settings_echo = data.get("settings") or {}
    results = data.get("results") or []

    subreddits = counts.get("subreddits")
    submissions = counts.get("submissions")
    res_len = len(results)

    if ok:
      logger and logger.info(
        f"✅ Fetch complete | subreddits={subreddits} submissions={submissions} results_len={res_len} "
        f"sort={settings_echo.get('sort')} time_filter={settings_echo.get('time_filter')} "
        f"limit={settings_echo.get('limit')} fields={settings_echo.get('fields')}"
      )
    else:
      logger and logger.warning(
        f"⚠️ Fetch returned ok=false | counts={counts} results_len={res_len}"
      )

  except requests.RequestException as e:
    logger and logger.exception(f"❌ Request error calling {url}: {e}")