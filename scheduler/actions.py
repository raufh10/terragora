import asyncio
import requests
from datetime import datetime, timezone
from services.database import (
  agendas,
  alerts,
  db,
  submissions
)

def do_extraction(logger):
  supabase = db.get_supabase_client()

  # --- Extract submissions data from API ---
  from services.config import settings
  api = getattr(settings, "API_ENDPOINT", None)
  if not api:
    logger.error("❌ Missing settings.API_ENDPOINT")
    return

  url = f"{api.rstrip('/')}/submissions/fetch"

  payload = [
    {
      "subreddit": "lakers",
      "limit": 1000,
      "sort": "new",
      "time_filter": "day",
      "fields": ["id", "title", "author", "score", "permalink", "created_utc"],
    },
    {
      "subreddit": "AEWOfficial",
      "limit": 1000,
      "sort": "new",
      "time_filter": "day",
      "fields": ["id", "title", "author", "score", "permalink", "created_utc"],
    },
    {
      "subreddit": "indotech",
      "limit": 1000,
      "sort": "new",
      "time_filter": "day",
      "fields": ["id", "title", "author", "score", "permalink", "created_utc"],
    },
  ]

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

    # --- Process submissions data to insert-ready state ---
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

    # --- Insert submissions data to supabase ---
    try:
      status = asyncio.run(submissions.insert(supabase, logger, to_insert_data))
    except Exception as e:
      logger.error(f"❌ Insert exception: {e}")

    if status:
      logger.info("📥 Insert is complete")

  except requests.RequestException as e:
    logger.exception(f"❌ Request error calling {url}: {e}")

def do_transform(logger):
  supabase = db.get_supabase_client()

  # --- Fetch agenda data from Supabase ---
  try:
    agenda = asyncio.run(agendas.select(supabase, logger, 1))
  except Exception as e:
    logger.error(f"❌ Insert exception: {e}")

  # --- Fetch relevant submissions data from Supabase ---
  try:
    submissions_data = asyncio.run(submissions.select(supabase, logger, agenda["data"]["subreddit"]))
  except Exception as e:
    logger.error(f"❌ Insert exception: {e}")

  # --- Process data to API's transform-ready state ---  
  payloads = []

  agenda_id = agenda["id"]
  agenda_type = agenda["type"]
  agenda_subreddit = agenda["data"]["subreddit"]
  agenda_prompt = agenda["data"]["prompt"]

  if agenda_type == "upvote":
    system_prompt = (
      "Your goal is to help generate Reddit replies that are likely to receive more upvotes. "
      "Focus on writing authentic, engaging, and contextually relevant responses aligned with the subreddit audience. "
      "Additionally, assess how relevant each post is to the given agenda prompt, providing a relevance score from 0 to 100."
    )

  for item in submissions_data:
    user_prompt = (
      f"You are writing a reply to a Reddit post in r/{agenda_subreddit}.\n\n"
      f"Post title: \"{item['data']['title']}\"\n"
      f"Current upvotes: {item['data']['score']}\n\n"
      f"Agenda context:\n{agenda_prompt}\n\n"
      "Write a thoughtful, engaging, and authentic reply that is likely to get upvoted "
      "by members of this subreddit. Focus on adding value to the discussion — "
      "for example, share useful insights, relatable experiences, or concise technical tips "
      "that align with the community’s interests.\n\n"
      "Additionally, evaluate how relevant this post is to the agenda context above. "
      "Provide a relevance score from 0 to 100, where 0 means completely unrelated "
      "and 100 means perfectly aligned with the agenda topic."
    )

    new_item = {
      "submission_id": item["id"],
      "agenda_id": agenda_id,
      "system_prompt": system_prompt,
      "user_prompt": user_prompt
    }
    payloads.append(new_item)

  payloads = payloads[:1]

  # --- Transform data using API ---
  from services.config import settings
  api = getattr(settings, "API_ENDPOINT", None)
  if not api:
    logger.error("❌ Missing settings.API_ENDPOINT")
    return

  url = f"{api.rstrip('/')}/analysis/run"
  all_results = []

  try:
    for payload in payloads:
      logger.info(f"📡 POST {url} | submission_id={payload['submission_id']}")
      try:
        resp = requests.post(url, json=payload, timeout=30)
      except requests.RequestException as e:
        logger.error(f"💥 Request error for submission_id={payload['submission_id']}: {e}")
        continue

      if not resp.ok:
        logger.error(f"⚠️ Transform failed [{resp.status_code}] → {resp.text[:200]}")
        continue

      try:
        data = resp.json()
      except ValueError:
        logger.error(f"⚠️ Invalid JSON response for submission_id={payload['submission_id']}")
        continue

      if not isinstance(data, dict) or not data:
        logger.warning(f"⚠️ No result or unexpected data shape for submission_id={payload['submission_id']}")
        continue

      data["agenda_id"] = payload["agenda_id"]
      data["submission_id"] = payload["submission_id"]
      all_results.append(data)

    if not all_results:
      logger.warning("⚠️ No transform results produced — skipping insert")
      return

    logger.info(f"✅ Transform complete | results_len={len(all_results)}")

    # --- Insert alert data to Supabase ---
    try:
      status = asyncio.run(alerts.insert(supabase, logger, all_results))
    except Exception as e:
      logger.error(f"❌ Insert exception: {e}")
      return

    if status:
      logger.info("📥 Insert is complete")

  except Exception as e:
    logger.exception(f"💥 Unexpected error in transform loop: {e}")

  except requests.RequestException as e:
    logger.exception(f"❌ Request error calling {url}: {e}")

def do_load(logger):
  supabase = db.get_supabase_client()

  # --- Fetch alerts data from Supabase ---
  try:
    alerts_data = asyncio.run(alerts.select(supabase, logger))
  except Exception as e:
    logger.error(f"❌ Insert exception: {e}")

  # --- Process alerts data to load-ready state ---
  to_load_data = []
  for item in alerts_data:
    sid = item.get("id")
    relevance = item.get("relevance")
    agenda_type = (item.get("messageagendas") or {}).get("type")

    sub = item.get("submissions") or {}
    data = sub.get("data") or {}
    subreddit = sub.get("subreddit")

    title = data.get("title")
    score = data.get("score")
    author = data.get("author")
    permalink = data.get("permalink")
    created_ts = data.get("created_utc")

    created_iso = (
      datetime.fromtimestamp(created_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
      if isinstance(created_ts, (int, float)) else "N/A"
    )

    message = (
      f"🔔 Alert — r/{subreddit} ({agenda_type or 'agenda'})\n"
      f"Title: {title}\n"
      f"Author: u/{author} • Score: {score}\n"
      f"Relevance: {relevance}%\n"
      f"Link: {permalink}\n"
      f"Created (UTC): {created_iso}"
    )
    to_load_data.append({"id": sid, "message": message})

  # --- Send alerts data using API ---
  from services.config import settings
  api = getattr(settings, "API_ENDPOINT", None)
  if not api:
    logger.error("❌ Missing settings.API_ENDPOINT")
    return

  url = f"{api.rstrip('/')}/telegram"
  logger.info(f"📡 Sending {len(to_load_data)} Telegram notifications → {url}")

  success_updates = []

  for row in to_load_data:
    sid = row.get("id")
    msg = row.get("message", "")

    if not msg:
      logger.warning(f"⚠️ Skipping id={sid}: empty message")
      continue

    try:
      resp = requests.post(url, json={"message": msg}, timeout=30)
    except requests.RequestException as e:
      logger.error(f"💥 Request error for id={sid}: {e}")
      continue

    if not resp.ok:
      preview = (msg[:120] + "…") if len(msg) > 120 else msg
      logger.error(f"🚫 Telegram send failed for id={sid} [{resp.status_code}] | preview={preview!r}")
      continue

    try:
      body = resp.json()
    except ValueError:
      logger.error(f"⚠️ Invalid JSON response for id={sid}")
      continue

    if bool(body.get("ok")):
      success_updates.append(sid)
      logger.info(f"✅ Telegram sent for id={sid}")
    else:
      logger.warning(f"⚠️ Telegram endpoint returned ok=false for id={sid}: {body}")

  logger.info(f"📬 Telegram send summary | success={len(success_updates)} / {len(to_load_data)}")

  # --- Update alerts data status in supabase ---
  try:
    status = asyncio.run(alerts.update_statuses_success(supabase, logger, success_updates))
  except Exception as e:
    logger.error(f"❌ Insert exception: {e}")

  if status:
    logger.info("📥 Insert is complete")
