from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Body

from services.config import credentials, settings
from services.extraction import (
  AsyncPrawStarter,
  RulesExtractor
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
    "fields": payload.get("fields") or getattr(
      settings,
      "RULE_FIELDS",
      ["short_name", "description", "kind", "violation_reason", "created_utc", "priority"],
    ),
  }
  return cfg

@router.post("/rules/fetch")
async def fetch_rules(
  config: Optional[Dict[str, Any]] = Body(None),
):
  logger.info("📥 Starting rules fetch workflow")
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
      totals = {"subreddits": len(subs_list), "rules": 0}

      for sr in subs_list:
        sr_cfg = {**cfg, "subreddit": sr}
        logger.debug(f"🔍 Collecting rules from r/{sr} | fields={sr_cfg['fields']}")
        extractor = RulesExtractor.from_config(reddit, logger, sr_cfg)
        rows = await extractor.collect()
        results[sr] = rows
        totals["rules"] += len(rows)

      logger.info(f"✅ Rules fetch complete | subreddits={totals['subreddits']} total_rules={totals['rules']}")
      return {
        "ok": True,
        "counts": totals,
        "results": results,
        "settings": {
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
    logger.exception("💥 Unhandled exception during rules fetch")
    raise HTTPException(status_code=500, detail="Internal server error")
