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
    keyword_map: Dict[str, Any] = payload.get("keyword_map") or {}

    model_name: str = str(payload.get("model_name", "all-MiniLM-L6-v2")).strip()
    thresh_lead: float = float(payload.get("thresh_lead", 0.58))
    thresh_related: float = float(payload.get("thresh_related", 0.55))
    thresh_qd: float = float(payload.get("thresh_qd", 0.52))
    preprocess: bool = bool(payload.get("preprocess", True))

    if not subreddit:
      logger.warning("⚠️ Missing 'subreddit'")
    if not text:
      logger.warning("⚠️ Missing 'text'")
    if not keyword_map:
      logger.warning("⚠️ Missing 'keyword_map'")

    if not subreddit or not text or not keyword_map:
      raise HTTPException(status_code=400, detail="subreddit, text, and keyword_map are required")

    logger.debug(
      f"Params | sub='{subreddit}' | text_len={len(text)} | "
      f"model={model_name} | thresholds={{lead:{thresh_lead}, related:{thresh_related}, qd:{thresh_qd}}} | "
      f"preprocess={preprocess}"
    )

    # Optional normalization/deduplication/lowercasing
    if preprocess:
      logger.debug("🔧 Preprocessing keyword_map via classmethod")
      keyword_map = RedditPostCategorizer.process_keywords(keyword_map)

    # Initialize categorizer
    categorizer = RedditPostCategorizer(
      keyword_map=keyword_map,
      model_name=model_name,
      thresh_lead=thresh_lead,
      thresh_related=thresh_related,
      thresh_qd=thresh_qd
    )

    # Run categorization
    logger.debug("🧠 Encoding & scoring post against categories")
    result = categorizer.categorize_post(subreddit, text)

    if not result or "category" not in result:
      logger.error("⚠️ Categorizer returned no result")
      raise HTTPException(status_code=502, detail="No categorization result")

    logger.info(f"✅ Labeling complete | category={result.get('category')} score={result.get('score')}")
    logger.debug(f"Scores breakdown: {result.get('scores', {})}")

    # Return minimal useful payload (echo inputs for traceability)
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
  except Exception:
    logger.exception("💥 Unhandled error in /label/run (RedditPostCategorizer)")
    raise HTTPException(status_code=500, detail="Internal server error")
