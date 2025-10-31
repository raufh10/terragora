import asyncio
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List

from services.database import agendas, alerts, db, submissions


def do_all(logger):
  """
  Fetches ALL agendas from Supabase and processes each sequentially:
  EXTRACT → TRANSFORM → LOAD
  """
  supabase = db.get_supabase_client()

  # --- Load configuration ---
  try:
    from services.config import settings
    api = getattr(settings, "API_ENDPOINT", None)
  except Exception:
    logger.exception("❌ Unable to import settings or read API_ENDPOINT")
    return
  if not api:
    logger.error("❌ Missing settings.API_ENDPOINT")
    return

  fetch_url = f"{api.rstrip('/')}/submissions/fetch"
  run_url = f"{api.rstrip('/')}/label/run"
  tg_url = f"{api.rstrip('/')}/telegram"

  # --- Fetch all agendas ---
  try:
    agenda_list = asyncio.run(agendas.select(supabase, logger)) or []
  except Exception as e:
    logger.error(f"❌ Agenda select exception: {e}")
    return

  if not agenda_list:
    logger.warning("⚠️ No agendas found in database")
    return

  logger.info(f"🗂️ Found {len(agenda_list)} agenda(s) to process")

  for idx, agenda in enumerate(agenda_list, start=1):
    try:
      logger.info(f"====== ▶️ Agenda {idx}/{len(agenda_list)} | id={agenda.get('id')} ======")
      _process_agenda(logger, supabase, agenda, fetch_url, run_url, tg_url)
    except Exception as e:
      logger.exception(f"💥 Unhandled error processing agenda id={agenda.get('id')}: {e}")
      continue


def _process_agenda(
  logger,
  supabase,
  agenda: Dict[str, Any],
  fetch_url: str,
  run_url: str,
  tg_url: str,
):
  """Performs EXTRACT → TRANSFORM → LOAD for a single agenda."""
  try:
    agenda_id = agenda["id"]
    data = agenda.get("data") or {}
    agenda_subreddit, agenda_keywords = next(iter(data.items()))

  except Exception:
    logger.exception("❌ Agenda missing required fields; skipping")
    return

  # =====================
  # 1️⃣ EXTRACT
  # =====================
  fetch_payload = {
    "subreddit": agenda_subreddit
  }

  all_insert_data = []
  try:
    logger.info(f"📡 POST {fetch_url} | subreddit={agenda_subreddit}")
    resp = requests.post(fetch_url, json=fetch_payload, timeout=30)
    if not resp.ok:
      logger.error(f"⚠️ Fetch failed [{resp.status_code}] → {resp.text[:300]}")
    else:
      try:
        body = resp.json()
      except ValueError:
        body = {}
        logger.error("⚠️ Invalid JSON response from fetch endpoint")

      ok = bool(body.get("ok"))
      results = body.get("results") or {}
      posts = results.get(agenda_subreddit) if isinstance(results, dict) else results
      if not ok or not posts:
        logger.warning(f"⚠️ No posts returned for r/{agenda_subreddit}")
      else:
        try:
          existing_ids = asyncio.run(submissions.select_reddit_ids(supabase, logger, agenda_subreddit))
        except Exception as e:
          logger.exception(f"❌ Failed reading existing reddit_ids: {e}")
          existing_ids = set()

        for post in posts:
          if not isinstance(post, dict):
            continue
          rid = post.get("id")
          if not rid or rid in existing_ids:
            continue
          new_post = dict(post)
          new_post.pop("id", None)
          all_insert_data.append({"reddit_id": rid, "subreddit": agenda_subreddit, "data": new_post})
  except requests.RequestException as e:
    logger.exception(f"❌ Request error calling fetch endpoint: {e}")

  if all_insert_data:
    try:
      status = asyncio.run(submissions.insert(supabase, logger, all_insert_data))
      if status:
        logger.info(f"📥 Insert complete | total_inserted={len(all_insert_data)}")
      else:
        logger.warning("⚠️ Insert returned falsy result")
    except Exception as e:
      logger.error(f"❌ Insert exception (submissions): {e}")
  else:
    logger.warning("⚠️ No valid submission data collected; skipping insert")

  # =====================
  # 2️⃣ TRANSFORM
  # =====================
  try:
    submissions_data = asyncio.run(submissions.select(supabase, logger, agenda_subreddit))
  except Exception as e:
    logger.error(f"❌ Submissions fetch exception: {e}")
    submissions_data = []

  try:
    existing_alerts_ids = asyncio.run(alerts.select_exists_ids(supabase, logger, agenda_id))
  except Exception as e:
    logger.error(f"❌ Existing alerts IDs fetch exception: {e}")
    existing_alerts_ids = set()

  new_submissions_data = [it for it in submissions_data if it.get("id") not in existing_alerts_ids]

  payloads = []
  for item in new_submissions_data:
    pdata = item.get("data") or {}
    title = pdata.get("title", "-")
    selftext = pdata.get("selftext", "")

    submissions_text = f"{title}\n{selftext}"
    payloads.append({
      "submission_id": item.get("id"),
      "subreddit": agenda_subreddit,
      "text": submissions_text,
      "keyword_map": agenda_keywords
    })

  all_results = []
  for payload in payloads:
    sid = payload.get("submission_id")
    if not sid:
      continue
    logger.info(f"📡 POST {run_url} | submission_id={sid}")
    try:
      resp = requests.post(run_url, json=payload, timeout=60)
    except requests.RequestException as e:
      logger.error(f"💥 Request error for submission_id={sid}: {e}")
      continue

    if not resp.ok:
      logger.error(f"⚠️ Transform failed [{resp.status_code}] → {resp.text[:200]}")
      continue

    try:
      data_out = resp.json()
    except ValueError:
      logger.error(f"⚠️ Invalid JSON response for submission_id={sid}")
      continue

    if not isinstance(data_out, dict) or not data_out:
      continue
    result = data_out.get("result")
    insert_result = {
      "agenda_id": agenda_id,
      "submission_id": sid
    }
    all_results.append(insert_result | result)

  if not all_results:
    logger.warning("⚠️ No transform results — skipping alerts insert/load for this agenda")
    return

  try:
    status = asyncio.run(alerts.insert(supabase, logger, all_results))
    if status:
      logger.info("📥 Alerts insert complete")
  except Exception as e:
    logger.error(f"❌ Alerts insert exception: {e}")

  # =====================
  # 3️⃣ LOAD
  # =====================
  try:
    alerts_data = asyncio.run(alerts.select(supabase, logger))
  except Exception as e:
    logger.error(f"❌ Alerts select exception: {e}")
    return

  to_load_data = []
  for item in alerts_data:

    sid = item.get("unique_key")
    suggestions = item.get("suggestions") or []
    category = suggestions.get("category", "Category Placeholder")
    score = suggestions.get("score", "Score Placeholder")
    scores = suggestions.get("scores", "Scores Placeholder")

    sub = item.get("submissions") or {}
    sdata = sub.get("data") or {}

    title = sdata.get("title", "-")
    author = sdata.get("author", "-")
    created_ts = sdata.get("created_utc")
    created_iso = (
      datetime.fromtimestamp(created_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
      if isinstance(created_ts, (int, float)) else "N/A"
    )

    suggestions_str = "\n".join([f"- {c.get('text', '').strip()}" for c in suggestions if c.get("text")]) or "- (no suggestions)"
    message = (
      f"🔔 Alert — r/{agenda_subreddit}\n"
      f"Title: {title}\n"
      f"Author: u/{author} • Score: {score}\n"
      f"Category: {category}\n"
      f"Score: {score}-{scores}\n"
      f"Created (UTC): {created_iso}"
    )
    to_load_data.append({"id": sid, "message": message})

  if not to_load_data:
    logger.info("ℹ️ No alerts to send for this agenda")
    return

  logger.info(f"📡 Sending {len(to_load_data)} Telegram notifications → {tg_url}")

  success_updates = []
  for row in to_load_data:
    sid = row.get("id")
    msg = row.get("message", "")
    if not msg:
      continue
    try:
      resp = requests.post(tg_url, json={"message": msg}, timeout=30)
      if resp.ok and resp.json().get("ok"):
        success_updates.append(sid)
        logger.info(f"✅ Telegram sent for id={sid}")
      else:
        logger.error(f"🚫 Telegram send failed for id={sid} [{resp.status_code}]")
    except Exception as e:
      logger.error(f"💥 Telegram send exception for id={sid}: {e}")

  if success_updates:
    try:
      status = asyncio.run(alerts.update_statuses_success(supabase, logger, success_updates))
      if status:
        logger.info(f"🗂️ Updated alert statuses | success={len(success_updates)}")
    except Exception as e:
      logger.error(f"❌ Alerts status update exception: {e}")
