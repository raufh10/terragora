import os
import json
import yaml
import asyncio
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional

from services.database import db, agendas, submissions

PROMPTS_PATH = "data/prompts.yaml"
def _load_prompts_yaml(logger, path: str = PROMPTS_PATH) -> Tuple[str, str]:
  try:
    with open(path, "r", encoding="utf-8") as f:
      data = yaml.safe_load(f)
  except Exception as e:
    logger.exception(f"❌ Unable to read or parse YAML at {path}")
    raise RuntimeError(f"Failed to read/parse prompts YAML: {e}") from e

  if not isinstance(data, dict):
    raise ValueError(f"Invalid YAML structure in {path}: expected a mapping at top-level")

  block = data.get("submission_category")
  if not isinstance(block, dict):
    raise ValueError("Missing required key 'submission_category' (mapping) in prompts YAML")

  system_prompt = block.get("system_prompt")
  user_prompt = block.get("user_prompt")

  if not isinstance(system_prompt, str) or not system_prompt.strip():
    raise ValueError("'submission_category.system_prompt' must be a non-empty string")

  if not isinstance(user_prompt, str) or not user_prompt.strip():
    raise ValueError("'submission_category.user_prompt' must be a non-empty string")

  return system_prompt.strip(), user_prompt.strip()

def do_all(logger):
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
  run_url = f"{api.rstrip('/')}/analysis/run"

  # --- Load prompts from YAML ---
  system_prompt, user_prompt_tpl = _load_prompts_yaml(logger, PROMPTS_PATH)
  logger.debug(
    f"🧾 Prompts loaded | system_len={len(system_prompt)} user_tpl_len={len(user_prompt_tpl)}"
  )

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
      _process_agenda(logger, supabase, agenda, fetch_url, run_url, system_prompt, user_prompt_tpl)
    except Exception as e:
      logger.exception(f"💥 Unhandled error processing agenda id={agenda.get('id')}: {e}")
      continue

def _process_agenda(
  logger,
  supabase,
  agenda: Dict[str, Any],
  fetch_url: str,
  run_url: str,
  system_prompt: str,
  user_prompt_tpl: str,
):
  try:
    agenda_id = agenda["id"]
    data = agenda.get("data") or {}

    agenda_subreddit = agenda.get("subreddit")
    if not agenda_subreddit:
      raise ValueError("Missing required field: subreddit")

  except Exception:
    logger.exception("❌ Agenda missing required fields; skipping")
    return

  # =====================
  # 1️⃣ EXTRACT
  # =====================
  fetch_payload = {"subreddit": agenda_subreddit}

  all_insert_data: List[Dict[str, Any]] = []
  try:
    logger.info(f"📡 POST {fetch_url} | subreddit={agenda_subreddit}")
    resp = requests.post(fetch_url, json=fetch_payload, timeout=60)
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
          existing_ids = set(existing_ids or [])
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
          all_insert_data.append({
            "reddit_id": rid,
            "subreddit": agenda_subreddit,
            "data": new_post
          })
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
  # 2️⃣ TRANSFORM (→ /analysis/run with prompts)
  # =====================
  try:
    submissions_data = asyncio.run(submissions.select_to_label(supabase, logger, agenda_subreddit))
  except Exception as e:
    logger.error(f"❌ Submissions fetch exception: {e}")
    submissions_data = []
  else:
    if submissions_data is None:
      submissions_data = []

  payloads: List[Dict[str, Any]] = []
  for item in submissions_data:
    pdata = item.get("data") or {}
    title = pdata.get("title", "-") or "-"
    selftext = pdata.get("selftext", "") or ""
    author = pdata.get("author", "unknown") or "unknown"
    created_ts = pdata.get("created_utc")
    created_iso = (
      datetime.fromtimestamp(created_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
      if isinstance(created_ts, (int, float)) else "N/A"
    )

    user_prompt = user_prompt_tpl.format(
      subreddit=agenda_subreddit,
      title=title,
      selftext=selftext,
      author=author,
      created_utc=created_iso
    ).strip()

    payloads.append({
      "submission_id": item.get("id"),
      "system_prompt": system_prompt,
      "user_prompt": user_prompt
    })

  all_results: List[Dict[str, Any]] = []
  for payload in payloads:
    sid = payload.get("submission_id")
    if not sid:
      continue
    logger.info(f"📡 POST {run_url} | submission_id={sid}")
    try:
      resp = requests.post(run_url, json={
        "system_prompt": payload["system_prompt"],
        "user_prompt": payload["user_prompt"]
      }, timeout=60)
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

    insert_result = {
      "submission_id": sid,
      "to_insert": {
        "category": data_out["label"],
        "category_data": {
          "confidence": data_out.get("confidence"),
          "rationale": data_out.get("rationale"),
        }
      }
    }
    all_results.append(insert_result)

  if not all_results:
    logger.warning("⚠️ No transform results — skipping updates for this agenda")
    return

  try:
    status = asyncio.run(submissions.update_category(supabase, logger, all_results))
    if status:
      logger.info("📥 Category updates complete")
  except Exception as e:
    logger.error(f"❌ Category update exception: {e}")
