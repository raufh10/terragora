import asyncio
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
import os

from services.database import agendas, alerts, db, submissions


PROMPTS_PATH = "data/prompts.md"


def _load_prompts(logger, path: str = PROMPTS_PATH) -> Tuple[str, str]:
  """
  Load system & user prompts from a markdown file.

  Supported markers inside data/prompts.md (any one will work):
    - HTML comments:
        <!-- SYSTEM_PROMPT_START -->
        ...system text...
        <!-- SYSTEM_PROMPT_END -->
        <!-- USER_PROMPT_START -->
        ...user template...
        <!-- USER_PROMPT_END -->

    - Headings:
        ## SubmissionCategory System
        ...system text...
        ## SubmissionCategory User
        ...user template...

    - Fallbacks:
        - Entire file becomes system prompt.
        - User prompt falls back to a safe template using placeholders.
  """
  system_prompt = ""
  user_prompt_tpl = ""

  try:
    with open(path, "r", encoding="utf-8") as f:
      content = f.read()
  except Exception:
    logger.exception(f"❌ Unable to read prompts file at {path}")
    # Fallbacks
    system_prompt = (
      "You are a Reddit post classifier that returns a JSON object with fields "
      "'label' (one of: lead, relevant, help, question, discussion), "
      "'confidence' (0–100), and 'rationale' (one concise sentence)."
    )
    user_prompt_tpl = (
      "Subreddit: r/{subreddit}\n"
      "Title: {title}\n"
      "Body: {selftext}\n"
      "Author: u/{author}\n"
      "Created_UTC: {created_utc}"
    )
    return system_prompt, user_prompt_tpl

  # Try HTML comment markers first
  def _extract_between(text: str, start_marker: str, end_marker: str) -> Optional[str]:
    start = text.find(start_marker)
    if start == -1:
      return None
    start += len(start_marker)
    end = text.find(end_marker, start)
    if end == -1:
      return None
    return text[start:end].strip()

  sys_from_comments = _extract_between(
    content, "<!-- SYSTEM_PROMPT_START -->", "<!-- SYSTEM_PROMPT_END -->"
  )
  user_from_comments = _extract_between(
    content, "<!-- USER_PROMPT_START -->", "<!-- USER_PROMPT_END -->"
  )

  if sys_from_comments or user_from_comments:
    system_prompt = (sys_from_comments or "").strip()
    user_prompt_tpl = (user_from_comments or "").strip()

  # If not found, try heading-based extraction
  if not system_prompt or not user_prompt_tpl:
    lines = content.splitlines()
    buff = []
    block = None
    system_block = []
    user_block = []

    def _is_sys_heading(s: str) -> bool:
      s = s.strip().lower()
      return ("submissioncategory" in s and "system" in s) or s.endswith("system")

    def _is_user_heading(s: str) -> bool:
      s = s.strip().lower()
      return ("submissioncategory" in s and "user" in s) or s.endswith("user")

    for ln in lines:
      if ln.strip().startswith("#"):  # heading
        if _is_sys_heading(ln):
          block = "system"
          continue
        if _is_user_heading(ln):
          block = "user"
          continue
        # other headings end any active block
        block = None
      else:
        if block == "system":
          system_block.append(ln)
        elif block == "user":
          user_block.append(ln)

    if not system_prompt and system_block:
      system_prompt = "\n".join(system_block).strip()
    if not user_prompt_tpl and user_block:
      user_prompt_tpl = "\n".join(user_block).strip()

  # Final fallbacks if still missing
  if not system_prompt:
    system_prompt = (
      "You are a Reddit post classifier that returns a JSON object with fields "
      "'label' (one of: lead, relevant, help, question, discussion), "
      "'confidence' (0–100), and 'rationale' (one concise sentence)."
    )
  if not user_prompt_tpl:
    user_prompt_tpl = (
      "Subreddit: r/{subreddit}\n"
      "Title: {title}\n"
      "Body: {selftext}\n"
      "Author: u/{author}\n"
      "Created_UTC: {created_utc}"
    )

  return system_prompt, user_prompt_tpl


def do_all(logger):
  """
  Fetches ALL agendas from Supabase and processes each sequentially:
  EXTRACT → TRANSFORM
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
  # ✅ switched to the new endpoint
  run_url = f"{api.rstrip('/')}/analysis/run"
  tg_url = f"{api.rstrip('/')}/telegram"

  # --- Load prompts from file ---
  system_prompt, user_prompt_tpl = _load_prompts(logger, PROMPTS_PATH)
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
      _process_agenda(logger, supabase, agenda, fetch_url, run_url, tg_url, system_prompt, user_prompt_tpl)
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
  system_prompt: str,
  user_prompt_tpl: str,
):
  """Performs EXTRACT → TRANSFORM for a single agenda."""
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
  fetch_payload = {"subreddit": agenda_subreddit}

  all_insert_data: List[Dict[str, Any]] = []
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
    submissions_data = asyncio.run(submissions.select(supabase, logger, agenda_subreddit))
  except Exception as e:
    logger.error(f"❌ Submissions fetch exception: {e}")
    submissions_data = []

  try:
    existing_alerts_ids = asyncio.run(alerts.select_exists_ids(supabase, logger, agenda_id))
    existing_alerts_ids = set(existing_alerts_ids or [])
  except Exception as e:
    logger.error(f"❌ Existing alerts IDs fetch exception: {e}")
    existing_alerts_ids = set()

  new_submissions_data = [
    it for it in submissions_data if it.get("id") not in existing_alerts_ids
  ]

  payloads: List[Dict[str, Any]] = []
  for item in new_submissions_data:
    pdata = item.get("data") or {}
    title = pdata.get("title", "-") or "-"
    selftext = pdata.get("selftext", "") or ""
    author = pdata.get("author", "unknown") or "unknown"
    created_ts = pdata.get("created_utc")
    created_iso = (
      datetime.fromtimestamp(created_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
      if isinstance(created_ts, (int, float)) else "N/A"
    )

    # Build the user prompt from template
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

    if not isinstance(data_out, dict) or not data_out:
      continue

    # The /analysis/run endpoint returns the SubmissionCategory model directly
    # e.g., {"label": "...", "confidence": 87.3, "rationale": "..."}
    result = data_out
    insert_result = {
      "agenda_id": agenda_id,
      "submission_id": sid
    }
    # Merge and collect for alerts.insert
    all_results.append(insert_result | {"suggestions": result, "relevance": 0})

  if not all_results:
    logger.warning("⚠️ No transform results — skipping alerts insert for this agenda")
    return

  try:
    status = asyncio.run(alerts.insert(supabase, logger, all_results))
    if status:
      logger.info("📥 Alerts insert complete")
  except Exception as e:
    logger.error(f"❌ Alerts insert exception: {e}")
