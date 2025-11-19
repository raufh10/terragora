from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Body
from services.config import credentials, settings
from services.extraction import (
  AsyncPrawStarter,
  SubmissionsExtractor
)
from logger import start_logger

router = APIRouter()
logger = start_logger()

def _preflight_check() -> None:
  if not credentials.CLIENT_ID:
    logger.error("🚫 Missing CLIENT_ID in credentials")
    raise HTTPException(status_code=500, detail="Server misconfiguration: missing CLIENT_ID")
  if credentials.CLIENT_SECRET is None:
    logger.warning("⚠️ CLIENT_SECRET is empty or not set")
  if not (settings.USER_AGENT or "").strip():
    logger.error("🚫 Missing USER_AGENT in settings")
    raise HTTPException(status_code=500, detail="Server misconfiguration: missing USER_AGENT")

async def _build_reddit():
  reddit = (
    AsyncPrawStarter(logger)
    .with_client(credentials.CLIENT_ID, credentials.CLIENT_SECRET)
    .with_user_agent(settings.USER_AGENT)
    .with_read_only(settings.IS_READ_ONLY)
    .with_timeout(getattr(settings, "TIMEOUT", 15))
  )
  return await reddit.build()

def _normalize_config(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
  payload = payload or {}
  cfg = {
    "subreddit": payload.get("subreddit") or getattr(settings, "DEFAULT_SUBREDDIT", None),
    "limit": int(payload.get("limit", getattr(settings, "LIMIT", 50))),
    "sort": (payload.get("sort") or getattr(settings, "SORT", "new")).lower(),
    "time_filter": (payload.get("time_filter") or getattr(settings, "TIME_FILTER", "hour")).lower(),
    "fields": payload.get("fields") or getattr(
      settings,
      "FIELDS",
      [
        "id",
        "title",
        "author",
        "link_flair_text",
        "score",
        "upvote_ratio",
        "num_comments",
        "comments",
        "created_utc",
        "is_self",
        "selftext",
        "url",
        "permalink",
      ],
    ),
  }
  return cfg

@router.post("/submissions/fetch")
async def fetch_submissions(
  config: Optional[Dict[str, Any]] = Body(None),
):
  logger.info("📥 Starting submissions fetch workflow")
  _preflight_check()
  try:
    cfg = _normalize_config(config)

    subs_list: List[str] = []
    if config and isinstance(config.get("subreddits"), list) and config.get("subreddits"):
      subs_list = [str(s).strip() for s in config["subreddits"] if str(s).strip()]
    elif cfg.get("subreddit"):
      subs_list = [cfg["subreddit"]]

    if not subs_list:
      logger.warning("⚠️ No subreddit provided in config and no default in settings")
      raise HTTPException(status_code=400, detail="No subreddit specified")

    reddit = await _build_reddit()
    try:
      results: Dict[str, List[Dict[str, Any]]] = {}
      totals = {"subreddits": len(subs_list), "submissions": 0}

      for sr in subs_list:
        sr_cfg = {**cfg, "subreddit": sr}
        logger.debug(
          f"🔍 Collecting from r/{sr} | sort={sr_cfg['sort']} | time={sr_cfg['time_filter']} | limit={sr_cfg['limit']}"
        )
        extractor = SubmissionsExtractor.from_config(reddit, logger, sr_cfg)
        rows = await extractor.collect()
        results[sr] = rows
        totals["submissions"] += len(rows)

      logger.info(f"✅ Fetch complete | subreddits={totals['subreddits']} submissions={totals['submissions']}")
      return {
        "ok": True,
        "counts": totals,
        "results": results,
        "settings": {
          "sort": cfg["sort"],
          "time_filter": cfg["time_filter"],
          "limit": cfg["limit"],
          "fields": cfg["fields"],
        },
      }
    finally:
      try:
        await reddit.close()
      except Exception:
        logger.debug("Reddit client close skipped/failed (already closed or not needed).")
  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled exception during submissions fetch")
    raise HTTPException(status_code=500, detail="Internal server error")
