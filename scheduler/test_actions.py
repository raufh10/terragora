import os
import json
import time
import asyncio
import requests
from typing import Dict, Any, List, Tuple
from services.database import db, agendas, submissions

def _chunk_into_n(lst: List[Any], n: int) -> List[List[Any]]:
  if n <= 0:
    return [lst]
  L = len(lst)
  if L == 0:
    return [[] for _ in range(n)]
  base = L // n
  rem = L % n
  chunks = []
  start = 0
  for i in range(n):
    size = base + (1 if i < rem else 0)
    end = start + size
    chunks.append(lst[start:end])
    start = end
  return chunks

def _chunked(items: List[Dict[str, Any]], size: int) -> List[List[Dict[str, Any]]]:
  if size <= 0:
    return [items]
  return [items[i:i+size] for i in range(0, len(items), size)]

# =========================
# 1) Fetch-only
# =========================
def test_fetch(logger) -> int:
  supabase = db.get_supabase_client()

  try:
    from services.config import settings
    api = getattr(settings, "API_ENDPOINT", None)
  except Exception:
    logger.exception("❌ Unable to import settings or read API_ENDPOINT")
    return 0
  if not api:
    logger.error("❌ Missing settings.API_ENDPOINT")
    return 0

  fetch_url = f"{api.rstrip('/')}/submissions/fetch"

  try:
    agenda_list = asyncio.run(agendas.select(supabase, logger)) or []
  except Exception as e:
    logger.error(f"❌ Agenda select exception: {e}")
    return 0

  if not agenda_list:
    logger.warning("⚠️ No agendas found in database")
    return 0

  logger.info(f"🗂️ (TEST_FETCH) Found {len(agenda_list)} agenda(s) to process")
  total_inserted = 0

  for idx, agenda in enumerate(agenda_list, start=1):
    try:
      logger.info(f"(TEST_FETCH) ▶️ Agenda {idx}/{len(agenda_list)} | id={agenda.get('id')}")
      agenda_subreddit = agenda.get("subreddit")
      if not agenda_subreddit:
        logger.warning("(TEST_FETCH) ⚠️ Missing required field: subreddit; skipping")
        continue

      fetch_payload = {"subreddit": agenda_subreddit, "limit": 1000, "time_filter": "month"}
      logger.info(f"(TEST_FETCH) 📡 POST {fetch_url} | subreddit={agenda_subreddit}")

      try:
        resp = requests.post(fetch_url, json=fetch_payload, timeout=3600)
      except requests.RequestException as e:
        logger.error(f"(TEST_FETCH) 💥 Request error: {e}")
        continue

      if not resp.ok:
        logger.error(f"(TEST_FETCH) ⚠️ Fetch failed [{resp.status_code}] → {resp.text[:300]}")
        continue

      try:
        body = resp.json()
      except ValueError:
        logger.error("(TEST_FETCH) ⚠️ Invalid JSON response from fetch endpoint")
        continue

      ok = bool(body.get("ok"))
      results = body.get("results") or {}
      posts = results.get(agenda_subreddit) if isinstance(results, dict) else results

      if not (ok and isinstance(posts, list) and posts):
        logger.warning(f"(TEST_FETCH) ⚠️ No posts returned for r/{agenda_subreddit}")
        continue

      try:
        existing_ids = asyncio.run(submissions.select_reddit_ids(supabase, logger, agenda_subreddit))
        existing_ids = set(existing_ids or [])
      except Exception as e:
        logger.exception(f"❌ Failed reading existing reddit_ids: {e}")
        existing_ids = set()

      all_insert_data: List[Dict[str, Any]] = []
      for post in posts:
        if not isinstance(post, dict):
          continue
        rid = post.get("id")
        if not rid or rid in existing_ids:
          continue
        new_post = dict(post)
        new_post.pop("id", None)
        all_insert_data.append({
          "reddit_id": rid,
          "subreddit": agenda_subreddit,
          "data": new_post
        })

      if not all_insert_data:
        logger.info(f"(TEST_FETCH) ℹ️ Nothing new to insert for r/{agenda_subreddit}")
        continue

      if len(all_insert_data) > 100:
        chunks = _chunked(all_insert_data, 100)
        logger.info(f"(TEST_FETCH) 🧩 Insert in chunks | total_rows={len(all_insert_data)} chunks={len(chunks)} size=10")
      else:
        chunks = [all_insert_data]

      for i, chunk in enumerate(chunks, start=1):
        try:
          status = asyncio.run(submissions.insert(supabase, logger, chunk))
          if status:
            total_inserted += len(chunk)
            logger.info(f"📥 Inserted chunk {i}/{len(chunks)} | rows={len(chunk)} | r/{agenda_subreddit}")
          else:
            logger.warning(f"⚠️ Insert returned falsy result for chunk {i}/{len(chunks)} | r/{agenda_subreddit}")
        except Exception as e:
          logger.error(f"❌ Insert exception (submissions) for chunk {i}/{len(chunks)}: {e}")

    except Exception as e:
      logger.exception(f"(TEST_FETCH) 💥 Unhandled error processing agenda id={agenda.get('id')}: {e}")
      continue

  logger.info(f"(TEST_FETCH) ✅ Done | total_inserted={total_inserted}")
  return total_inserted

# =========================
# 2) Transform-only (use existing_posts chunk)
# =========================
def test_transform(
  logger,
  posts_chunk: List[Dict[str, Any]],
) -> Tuple[int, List[Dict[str, Any]]]:

  # --- Load configuration ---
  try:
    from services.config import settings
    api = getattr(settings, "API_ENDPOINT", None)
  except Exception:
    logger.exception("❌ Unable to import settings or read API_ENDPOINT")
    return 0
  if not api:
    logger.error("❌ Missing settings.API_ENDPOINT")
    return 0

  run_url = f"{api.rstrip('/')}/analysis/test"

  # Inline prompts
  system_prompt = (
    "You are a Reddit post classifier that determines whether a post is a potential business lead. "
    "Return a JSON object with these fields: "
    "'is_lead' (boolean) — True if the post indicates a request for a service or business opportunity, False if it's general discussion; "
    "'label' (string enum) — if is_lead=True, choose one from these categories: "
    "['personal_trainer', 'nutrition_coach', 'massage_therapist', 'yoga_instructor', 'physical_therapist', 'mindfulness_instructor', "
    "'auto_mechanic', 'car_detailer', 'landscaper', 'pressure_washing', 'electrician', 'plumber', 'hvac_technician', 'flooring_installer', "
    "'roofing_specialist', 'real_estate_agent']; "
    "if is_lead=False, use one of ['discussion', 'question', 'help', 'other']; "
    "'confidence' (number 0–100) — a numeric confidence score reflecting how certain you are about the classification."
  )
  user_prompt_tpl = (
    "Title: {title}\n"
    "Body: {selftext}\n"
  )

  total_classified = 0

  if not posts_chunk:
    logger.info("(TEST_TRANSFORM) ℹ️ Empty chunk; nothing to classify this loop")
    return 0

  logger.info(f"(TEST_TRANSFORM) 🔎 Classifying {len(posts_chunk)} post(s) from provided chunk")

  data_to_insert = []
  for row in posts_chunk:
    try:
      pdata = (row.get("data") or {})
      title = pdata.get("title", "-") or "-"
      selftext = pdata.get("selftext", "") or ""

      user_prompt = user_prompt_tpl.format(
        title=title,
        selftext=selftext,
      ).strip()

      sid = row.get("reddit_id")
      if not sid:
        logger.warning("(TEST_TRANSFORM) ⚠️ Missing reddit_id/id in post row; skipping")
        continue

      logger.info(f"(TEST_TRANSFORM) 📡 POST {run_url} | submission_id={sid}")
      try:
        resp = requests.post(run_url, json={
          "system_prompt": system_prompt,
          "user_prompt": user_prompt
        }, timeout=120)
      except requests.RequestException as e:
        logger.error(f"(TEST_TRANSFORM) 💥 Request error for submission_id={sid}: {e}")
        continue

      if not resp.ok:
        logger.error(f"(TEST_TRANSFORM) ⚠️ Transform failed [{resp.status_code}] → {resp.text[:200]}")
        continue

      try:
        data_out = resp.json()
      except ValueError:
        logger.error(f"(TEST_TRANSFORM) ⚠️ Invalid JSON response for submission_id={sid}")
        continue

      data_to_insert.append({
        "submission_id": sid,
        "to_insert": {
          "test_data": data_out
        }
      })
      total_classified += 1
      time.sleep(1)

    except Exception as e:
      logger.exception(f"(TEST_TRANSFORM) 💥 Unhandled error on a post row: {e}")
      continue

  # Update submissions table
  if asyncio.run(submissions.update_test_data(db.get_supabase_client(), logger, data_to_insert)):
    logger.info(f"(TEST_TRANSFORM) ✅ Done chunk | classified={total_classified}")
    return total_classified

# =========================
# Main Test Orchestrator
# =========================
def do_test(logger):

  # Decide whether to fetch
  not_fetching = True

  fetched_count = 0
  if not_fetching:
    logger.info(f"(TEST) 🚦 Skipping fetch.")
  else:
    fetched_count = test_fetch(logger)
    logger.info(f"(TEST) 🚦 Total fetched: {fetched_count}.")

  # Split into 10 chunks
  existing_posts = asyncio.run(submissions.select_non_test(db.get_supabase_client(), logger, "Rochester")) or []

  if existing_posts:
    chunks = _chunk_into_n(existing_posts, 25)
    logger.info(f"(TEST) 🧩 Prepared {len(chunks)} chunk(s) for transform")

    total_classified = 0
    for loop_idx, posts_chunk in enumerate(chunks, start=1):
      logger.info(f"🔁 (TEST_LOOP {loop_idx}/10) Transforming {len(posts_chunk)} post(s)...")
      classified = test_transform(logger, posts_chunk)
      total_classified += classified
      logger.info("⏳ Sleeping 30 seconds before next test_transform loop.")
      time.sleep(30)

    logger.info(f"✅ (TEST) Finished | fetched={fetched_count} | classified_total={total_classified}")
