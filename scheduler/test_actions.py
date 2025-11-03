import os
import json
import time
import asyncio
import requests
from typing import Dict, Any, List, Tuple

from services.database import db, agendas, submissions  # agendas used in fetch; submissions unused in transform now

DATA_DIR = "data"
TEST_POSTS_PATH = os.path.join(DATA_DIR, "testing_post.json")  # fetched posts
TEST_RESULTS_PATH = os.path.join(DATA_DIR, "test.json")        # classification outputs


# ---------- Helpers ----------
def _ensure_data_dir(logger) -> None:
  try:
    os.makedirs(DATA_DIR, exist_ok=True)
  except Exception as e:
    logger.error(f"❌ Failed ensuring data dir '{DATA_DIR}': {e}")
    raise

def _load_json_list(logger, path: str) -> List[Dict[str, Any]]:
  if not os.path.exists(path):
    return []
  try:
    with open(path, "r", encoding="utf-8") as f:
      data = json.load(f)
    if isinstance(data, list):
      return data
    logger.warning(f"⚠️ {path} is not a list; starting fresh []")
  except Exception as e:
    logger.warning(f"⚠️ Failed reading {path}; starting fresh []. Error: {e}")
  return []

def _write_json_list(logger, path: str, data: List[Dict[str, Any]]) -> None:
  try:
    with open(path, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"💾 Wrote {len(data)} records to {path}")
  except Exception as e:
    logger.error(f"❌ Failed writing {path}: {e}")

def _chunk_into_n(lst: List[Any], n: int) -> List[List[Any]]:
  """
  Split list into N nearly-equal chunks (some chunks may be empty if len(lst) < n).
  """
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


# =========================
# 1) Fetch-only (append posts into provided list)
# =========================
def test_fetch(logger, existing_posts: List[Dict[str, Any]]) -> Tuple[int, List[Dict[str, Any]]]:
  """
  Fetch posts per agenda (via /submissions/fetch) and append them to 'existing_posts'.
  Returns (appended_count, updated_posts_list)
  """
  supabase = db.get_supabase_client()

  # --- Load configuration ---
  try:
    from services.config import settings
    api = getattr(settings, "API_ENDPOINT", None)
  except Exception:
    logger.exception("❌ Unable to import settings or read API_ENDPOINT")
    return 0, existing_posts
  if not api:
    logger.error("❌ Missing settings.API_ENDPOINT")
    return 0, existing_posts

  fetch_url = f"{api.rstrip('/')}/submissions/fetch"

  # --- Fetch all agendas ---
  try:
    agenda_list = asyncio.run(agendas.select(supabase, logger)) or []
  except Exception as e:
    logger.error(f"❌ Agenda select exception: {e}")
    return 0, existing_posts

  if not agenda_list:
    logger.warning("⚠️ No agendas found in database")
    return 0, existing_posts

  logger.info(f"🗂️ (TEST_FETCH) Found {len(agenda_list)} agenda(s) to process")

  total_appended = 0

  for idx, agenda in enumerate(agenda_list, start=1):
    try:
      logger.info(f"(TEST_FETCH) ▶️ Agenda {idx}/{len(agenda_list)} | id={agenda.get('id')}")
      agenda_subreddit = agenda.get("subreddit")
      if not agenda_subreddit:
        logger.warning("(TEST_FETCH) ⚠️ Missing required field: subreddit; skipping")
        continue

      # EXTRACT: call /submissions/fetch
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

      if ok and isinstance(posts, list) and posts:
        appended = 0
        for post in posts:
          if not isinstance(post, dict):
            continue
          rid = post.get("id")
          new_post = dict(post)
          new_post.pop("id", None)
          existing_posts.append({
            "reddit_id": rid,
            "subreddit": agenda_subreddit,
            "data": new_post
          })
          appended += 1
        total_appended += appended
        logger.info(f"(TEST_FETCH) 🗄️ Appended {appended} post(s) for r/{agenda_subreddit}")
      else:
        logger.warning(f"(TEST_FETCH) ⚠️ No posts returned for r/{agenda_subreddit}")

    except Exception as e:
      logger.exception(f"(TEST_FETCH) 💥 Unhandled error processing agenda id={agenda.get('id')}: {e}")
      continue

  logger.info(f"(TEST_FETCH) ✅ Done | total_appended={total_appended}")
  return total_appended, existing_posts


# =========================
# 2) Transform-only (use existing_posts chunk)
# =========================
def test_transform(
  logger,
  existing_results: List[Dict[str, Any]],
  posts_chunk: List[Dict[str, Any]],
) -> Tuple[int, List[Dict[str, Any]]]:
  """
  Classify posts from 'posts_chunk' using /analysis/test and append outputs to 'existing_results'.
  Each element of posts_chunk is expected to be:
    { "reddit_id": ..., "subreddit": ..., "data": { "title": ..., "selftext": ... } }
  Returns (classified_count, updated_results_list)
  """
  # --- Load configuration ---
  try:
    from services.config import settings
    api = getattr(settings, "API_ENDPOINT", None)
  except Exception:
    logger.exception("❌ Unable to import settings or read API_ENDPOINT")
    return 0, existing_results
  if not api:
    logger.error("❌ Missing settings.API_ENDPOINT")
    return 0, existing_results

  run_url = f"{api.rstrip('/')}/analysis/test"

  # Inline prompts
  system_prompt = (
    "You are a Reddit post classifier that analyzes whether a post is a potential business lead. "
    "Return JSON with the following fields: "
    "'is_lead' (boolean) — True if the post indicates a specific service or business request; "
    "'label' (string) — if is_lead=True, describe the business or service type (e.g. 'roof repair', 'tree removal'); "
    "if is_lead=False, provide a general category like 'discussion' or 'question'; "
    "'confidence' (number 0–100) — indicating how certain you are in the classification."
  )
  user_prompt_tpl = (
    "Title: {title}\n"
    "Body: {selftext}\n"
  )

  total_classified = 0

  if not posts_chunk:
    logger.info("(TEST_TRANSFORM) ℹ️ Empty chunk; nothing to classify this loop")
    return 0, existing_results

  logger.info(f"(TEST_TRANSFORM) 🔎 Classifying {len(posts_chunk)} post(s) from provided chunk")

  for row in posts_chunk:
    try:
      pdata = (row.get("data") or {})
      title = pdata.get("title", "-") or "-"
      selftext = pdata.get("selftext", "") or ""

      user_prompt = user_prompt_tpl.format(
        title=title,
        selftext=selftext,
      ).strip()

      sid = row.get("reddit_id") or row.get("id")  # prefer reddit_id
      if not sid:
        logger.warning("(TEST_TRANSFORM) ⚠️ Missing reddit_id/id in post row; skipping")
        continue

      logger.info(f"(TEST_TRANSFORM) 📡 POST {run_url} | submission_id={sid}")
      try:
        resp = requests.post(run_url, json={
          "system_prompt": system_prompt,
          "user_prompt": user_prompt
        }, timeout=60)
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

      existing_results.append({
        "submission_id": sid,
        "data": data_out
      })
      total_classified += 1

    except Exception as e:
      logger.exception(f"(TEST_TRANSFORM) 💥 Unhandled error on a post row: {e}")
      continue

  logger.info(f"(TEST_TRANSFORM) ✅ Done chunk | classified={total_classified}")
  return total_classified, existing_results


# =========================
# Main Test Orchestrator
# =========================
def do_test(logger):
  """
  Orchestrates test flow:
    - Ensure dirs & load JSON state (posts, results).
    - If >100 posts already exist, skip fetch; otherwise fetch new posts.
    - Split existing_posts into 10 chunks.
    - For 10 loops:
        - classify the corresponding chunk via test_transform
        - write results after each loop
        - sleep 30s between loops
  """
  # Ensure dir & load
  _ensure_data_dir(logger)
  existing_posts: List[Dict[str, Any]] = _load_json_list(logger, TEST_POSTS_PATH)
  existing_results: List[Dict[str, Any]] = _load_json_list(logger, TEST_RESULTS_PATH)

  # Decide whether to fetch
  fetched_count = 0
  if len(existing_posts) > 100:
    logger.info(f"(TEST) 🚦 Found {len(existing_posts)} posts in {TEST_POSTS_PATH}; skipping fetch.")
  else:
    fetched_count, existing_posts = test_fetch(logger, existing_posts)
    _write_json_list(logger, TEST_POSTS_PATH, existing_posts)  # persist posts after fetch

  # Always re-read posts to ensure we chunk the latest list (optional, but safe)
  existing_posts = _load_json_list(logger, TEST_POSTS_PATH)

  """
  # Split into 10 chunks
  chunks = _chunk_into_n(existing_posts, 10)
  logger.info(f"(TEST) 🧩 Prepared {len(chunks)} chunk(s) for transform")

  total_classified = 0
  for loop_idx, posts_chunk in enumerate(chunks, start=1):
    logger.info(f"🔁 (TEST_LOOP {loop_idx}/10) Transforming {len(posts_chunk)} post(s)...")
    classified, existing_results = test_transform(logger, existing_results, posts_chunk)
    total_classified += classified
    _write_json_list(logger, TEST_RESULTS_PATH, existing_results)

    if loop_idx < 10:
      logger.info("⏳ Sleeping 30 seconds before next test_transform loop...")
      time.sleep(30)

  logger.info(f"✅ (TEST) Finished | fetched={fetched_count} | classified_total={total_classified}")
  """
