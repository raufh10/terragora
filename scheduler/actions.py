import asyncio
import requests
from datetime import datetime, timezone
from services.database import agendas, alerts, db, submissions

def do_all(logger):
  supabase = db.get_supabase_client()

  # =========
  # SETTINGS
  # =========
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
  tg_url = f"{api.rstrip('/')}/telegram"

  # ======================
  # 0) LOAD AGENDA (id=1)
  # ======================
  try:
    agenda = asyncio.run(agendas.select(supabase, logger, 1))  # agenda id = 1
  except Exception as e:
    logger.error(f"❌ Agenda fetch exception: {e}")
    return

  # agenda.data expected:
  # {
  #   "subreddit": "lakers",
  #   "prompt": "...",
  #   "extraction_data": { "limit": 100, "sort": "new", "time_filter": "hour", "fields": [...] }
  # }
  try:
    agenda_id = agenda["id"]
    data = agenda.get("data") or {}
    agenda_subreddit = data.get("subreddit", "lakers")
    agenda_prompt = data.get("prompt", "")
    extraction_data = data.get("extraction_data") or {}
    # sensible defaults if missing
    limit = int(extraction_data.get("limit", 100))
    sort = extraction_data.get("sort", "new")
    time_filter = extraction_data.get("time_filter", "hour")
    fields = extraction_data.get("fields") or ["id", "title", "author", "score", "permalink", "created_utc"]
  except Exception:
    logger.exception("❌ Agenda object missing expected fields")
    return

  # ====================================
  # 1) EXTRACT using agenda.extraction_data
  # ====================================
  # Build fetch payload *from agenda data*
  fetch_payload = {
    "subreddit": agenda_subreddit,
    "limit": limit,
    "sort": sort,
    "time_filter": time_filter,
    "fields": fields,
    "prompt": agenda_prompt,  # include the agenda prompt in fetch request (as you wanted)
  }

  all_insert_data = []
  try:
    logger.info(f"📡 POST {fetch_url} | subreddit={agenda_subreddit} | sort={sort} | limit={limit} | time_filter={time_filter}")
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
      counts = body.get("counts") or {}
      results = body.get("results") or {}
      settings_echo = body.get("settings") or {}

      if not ok:
        logger.warning(f"⚠️ Fetch returned ok=false | counts={counts} results_type={type(results)}")
      else:
        logger.info(
          f"✅ Fetch complete | submissions={counts.get('submissions')} "
          f"sort={settings_echo.get('sort')} time_filter={settings_echo.get('time_filter')} limit={settings_echo.get('limit')}"
        )

        posts = results.get(agenda_subreddit) if isinstance(results, dict) else results
        if not posts:
          logger.warning(f"⚠️ No posts returned for subreddit={agenda_subreddit}")
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
    logger.exception(f"❌ Request error calling {fetch_url}: {e}")
  except Exception as e:
    logger.exception(f"💥 Unexpected error during extraction: {e}")

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
    logger.warning("⚠️ No valid submission data collected; skipping insert (continuing)")

  # =============================
  # 2) TRANSFORM (label) — reuse agenda.extraction_data + prompt
  # =============================
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

  # Top 5 most upvoted
  try:
    top5 = sorted(new_submissions_data, key=lambda x: (x.get("data") or {}).get("score", 0), reverse=True)[:5]
  except Exception:
    logger.exception("❌ Failed to sort/select top 5 submissions")
    top5 = []

  # Prompts
  system_prompt = (
    "Your goal is to help assess how relevant each post is to the given agenda prompt, "
    "providing a relevance score from 0 to 100. Additionally, generate 5 comment ideas "
    "that align with the agenda prompt."
  )

  payloads = []
  for item in top5:
    pdata = item.get("data") or {}
    title = pdata.get("title", "-")
    score = pdata.get("score", 0)
    user_prompt = (
      f"You are assessing a Reddit post in r/{agenda_subreddit}.\n\n"
      f"Post title: \"{title}\"\n"
      f"Current upvotes: {score}\n\n"
      f"Agenda context:\n{agenda_prompt}\n\n"
    )
    # Reuse agenda.extraction_data in the analysis payload for traceability
    payloads.append({
      "submission_id": item.get("id"),
      "agenda_id": agenda_id,
      "system_prompt": system_prompt,
      "user_prompt": user_prompt,
      "prompt": agenda_prompt,               # reuse prompt again
      "extraction_data": extraction_data,    # reuse extraction config again
      "subreddit": agenda_subreddit
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
      logger.warning(f"⚠️ No result or unexpected data shape for submission_id={sid}")
      continue

    data_out["agenda_id"] = agenda_id
    data_out["submission_id"] = sid
    all_results.append(data_out)

  if not all_results:
    logger.warning("⚠️ No transform results produced — skipping alerts insert and load step")
    return

  logger.info(f"✅ Transform complete | results_len={len(all_results)}")

  try:
    status = asyncio.run(alerts.insert(supabase, logger, all_results))
    if status:
      logger.info("📥 Alerts insert complete")
    else:
      logger.warning("⚠️ Alerts insert returned falsy result")
  except Exception as e:
    logger.error(f"❌ Alerts insert exception: {e}")

  # =========
  # 3) LOAD
  # =========
  try:
    alerts_data = asyncio.run(alerts.select(supabase, logger))
  except Exception as e:
    logger.error(f"❌ Alerts select exception: {e}")
    return

  to_load_data = []
  for item in alerts_data:
    try:
      relevance = item.get("relevance", 0)
      if relevance is None or relevance < 50:
        continue

      sid = item.get("unique_key") or item.get("submission_id") or item.get("id")
      suggestions = item.get("suggestions") or []

      sub = item.get("submissions") or {}
      subreddit = sub.get("subreddit", agenda_subreddit)
      sdata = sub.get("data") or {}

      title = sdata.get("title", "-")
      author = sdata.get("author", "-")
      score = sdata.get("score", 0)
      permalink = sdata.get("permalink", "-")
      created_ts = sdata.get("created_utc")

      created_iso = (
        datetime.fromtimestamp(created_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
        if isinstance(created_ts, (int, float)) else "N/A"
      )

      # Build suggestions safely (avoid f-string quote issues)
      suggestion_lines = []
      for c in suggestions:
        try:
          txt = (c.get("text") or "").strip()
          if txt:
            suggestion_lines.append(f"- {txt}")
        except Exception:
          continue
      suggestions_str = "\n".join(suggestion_lines) if suggestion_lines else "- (no suggestions)"

      message = (
        f"🔔 Alert — r/{subreddit}\n"
        f"Title: {title}\n"
        f"Author: u/{author} • Score: {score}\n"
        f"Relevance: {relevance}%\n"
        f"Link: {permalink}\n"
        f"Suggestions\n{suggestions_str}\n"
        f"Created (UTC): {created_iso}"
      )

      to_load_data.append({"id": sid, "message": message})
    except Exception:
      logger.exception("❌ Failed to build load payload for an alert row")
      continue

  logger.info(f"📡 Sending {len(to_load_data)} Telegram notifications → {tg_url}")

  success_updates = []
  for row in to_load_data:
    sid = row.get("id")
    msg = row.get("message", "")
    if not msg:
      logger.warning(f"⚠️ Skipping id={sid}: empty message")
      continue

    try:
      resp = requests.post(tg_url, json={"message": msg}, timeout=30)
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

  if success_updates:
    try:
      status = asyncio.run(alerts.update_statuses_success(supabase, logger, success_updates))
      if status:
        logger.info("🗂️ Updated alert statuses to success")
    except Exception as e:
      logger.error(f"❌ Alerts status update exception: {e}")
