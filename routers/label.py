from typing import Optional, Dict, Any
from fastapi import APIRouter, Body, HTTPException

from services.label import RedditPostCategorizer
from logger import start_logger

logger = start_logger()
router = APIRouter()

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

    # --- Guard checks ---
    if not subreddit:
      logger.warning("⚠️ Missing 'subreddit'")
    if not text:
      logger.warning("⚠️ Missing 'text'")
    if not keyword_map:
      logger.warning("⚠️ Missing 'keyword_map'")

    if not subreddit or not text or not keyword_map:
      raise HTTPException(status_code=400, detail="subreddit, text, and keyword_map are required")

    if not isinstance(keyword_map, dict):
      logger.error(f"❌ Invalid keyword_map type={type(keyword_map).__name__}, expected dict")
      raise HTTPException(status_code=400, detail="keyword_map must be a JSON object")

    if subreddit not in keyword_map:
      logger.warning(f"⚠️ Subreddit '{subreddit}' not found in keyword_map keys={list(keyword_map.keys())}")
      raise HTTPException(status_code=400, detail=f"'{subreddit}' not found in keyword_map")

    logger.debug(
      f"Params | sub='{subreddit}' | text_len={len(text)} | "
      f"model={model_name} | thresholds={{lead:{thresh_lead}, related:{thresh_related}, qd:{thresh_qd}}} | "
      f"preprocess={preprocess}"
    )

    # --- Preprocess keywords safely ---
    if preprocess:
      try:
        logger.debug("🔧 Preprocessing keyword_map via classmethod")
        keyword_map = RedditPostCategorizer.process_keywords(keyword_map)
      except Exception as e:
        logger.exception(f"💥 Failed processing keyword_map: {e}")
        raise HTTPException(status_code=400, detail="Invalid keyword_map structure")

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
