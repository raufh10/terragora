from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException

from services.config import credentials, settings

from services.label import RedditPostCategorizer
from services.extraction import (
  AsyncPrawStarter,
  RulesExtractor
)

from logger import start_logger
logger = start_logger()
router = APIRouter()

EXPECTED_CATEGORY_KEYS = {"lead", "related", "question-help", "discussion"}

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

@router.post("/label/run")
async def run_labeling(
  payload: Optional[Dict[str, Any]] = Body(None),
):
  logger.info("📥 Starting /label/run (RedditPostCategorizer)")
  try:
    payload = payload or {}

    subreddit: str = str(payload.get("subreddit", "")).strip()
    text: str = str(payload.get("text", "")).strip()
    keyword_map: Any = payload.get("keyword_map")

    model_name: str = str(payload.get("model_name", "all-MiniLM-L6-v2")).strip()
    thresh_lead: float = float(payload.get("thresh_lead", 0.58))
    thresh_related: float = float(payload.get("thresh_related", 0.55))
    thresh_qd: float = float(payload.get("thresh_qd", 0.52))
    preprocess: bool = bool(payload.get("preprocess", True))

    # --- Guard checks (required fields) ---
    if not subreddit or not text or not keyword_map:
      missing = [k for k, v in [("subreddit", subreddit), ("text", text), ("keyword_map", keyword_map)] if not v]
      logger.warning(f"⚠️ Missing required fields: {', '.join(missing)}")
      raise HTTPException(status_code=400, detail="subreddit, text, and keyword_map are required")

    if not isinstance(keyword_map, dict):
      logger.error(f"❌ Invalid keyword_map type={type(keyword_map).__name__}, expected dict")
      raise HTTPException(status_code=400, detail="keyword_map must be a JSON object")

    # --- Accept both shapes:
    #     A) {"Rochester": {lead:..., related:...}}
    #     B) {lead:..., related:...}  -> auto-wrap under subreddit
    if subreddit not in keyword_map:
      top_keys = set(map(str, keyword_map.keys()))
      if EXPECTED_CATEGORY_KEYS & top_keys:
        logger.warning(
          f"🔁 Auto-wrapping keyword_map under subreddit='{subreddit}' "
          f"(top-level keys looked like categories: {sorted(top_keys)})"
        )
        keyword_map = {subreddit: keyword_map}
      else:
        logger.warning(f"⚠️ Subreddit '{subreddit}' not found in keyword_map keys={list(keyword_map.keys())}")
        raise HTTPException(status_code=400, detail=f"'{subreddit}' not found in keyword_map")

    logger.debug(
      f"Params | sub='{subreddit}' | text_len={len(text)} | "
      f"model={model_name} | thresholds={{lead:{thresh_lead}, related:{thresh_related}, qd:{thresh_qd}}} | "
      f"preprocess={preprocess}"
    )

    # --- Preprocess keywords safely (defensive against lists / light-heavy) ---
    if preprocess:
      try:
        logger.debug("🔧 Preprocessing keyword_map via classmethod")
        keyword_map = RedditPostCategorizer.process_keywords(keyword_map)
      except Exception as e:
        logger.exception(f"💥 Failed processing keyword_map: {e}")
        raise HTTPException(status_code=400, detail="Invalid keyword_map structure")

    # Ensure the subreddit still exists post-processing
    if subreddit not in keyword_map:
      logger.error(f"❌ Subreddit '{subreddit}' missing after processing")
      raise HTTPException(status_code=400, detail=f"'{subreddit}' missing after keyword processing")

    # --- Initialize categorizer ---
    try:
      categorizer = RedditPostCategorizer(
        keyword_map=keyword_map,
        model_name=model_name,
        thresh_lead=thresh_lead,
        thresh_related=thresh_related,
        thresh_qd=thresh_qd
      )
    except Exception as e:
      logger.exception(f"💥 Failed initializing RedditPostCategorizer: {e}")
      raise HTTPException(status_code=500, detail="Failed to initialize categorizer")

    # --- Run categorization safely ---
    try:
      logger.debug("🧠 Encoding & scoring post against categories")
      result = categorizer.categorize_post(subreddit, text)
    except Exception as e:
      logger.exception(f"💥 Categorization error: {e}")
      raise HTTPException(status_code=500, detail="Categorization process failed")

    if not result or "category" not in result:
      logger.error("⚠️ Categorizer returned no valid result")
      raise HTTPException(status_code=502, detail="No categorization result")

    logger.info(f"✅ Labeling complete | category={result.get('category')} score={result.get('score')}")
    logger.debug(f"Scores breakdown: {result.get('scores', {})}")

    # --- Return response ---
    return {
      "input": {
        "subreddit": subreddit,
        "text_length": len(text),
        "model_name": model_name,
        "thresholds": {
          "lead": thresh_lead,
          "related": thresh_related,
          "question_discussion": thresh_qd
        },
        "preprocess": preprocess
      },
      "result": {
        "relevance": 0,
        "suggestions": result
      }
    }

  except HTTPException:
    raise
  except Exception as e:
    logger.exception(f"💥 Unhandled error in /label/run (RedditPostCategorizer): {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
