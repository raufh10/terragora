from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException

from services.llm import OpenAIResponse
from services.schemas import DiscoverCategory, NBAThreadCategory

from logger import start_logger
logger = start_logger()
router = APIRouter()

@router.post("/analysis/run")
async def run_analysis(
  payload: Optional[Dict[str, Any]] = Body(None),
):

  active_model = NBAThreadCategory
  logger.info("📥 Starting /analysis/run ({active_model})")

  try:
    payload = payload or {}
    system_prompt = str(payload.get("system_prompt", "")).strip()
    user_prompt = str(payload.get("user_prompt", "")).strip()

    if not system_prompt:
      logger.warning("⚠️ Missing system_prompt for {active_model} generation")
    if not user_prompt:
      logger.warning("⚠️ Missing user_prompt for {active_model} generation")

    logger.debug(f"Prompt lengths | system={len(system_prompt)} user={len(user_prompt)}")

    llm = OpenAIResponse()
    result = llm.generate_structured_response(
      logger,
      system_prompt,
      user_prompt,
      response_format=active_model
    )

    if not result:
      logger.error("⚠️ LLM returned no structured result ({active_model})")
      raise HTTPException(status_code=502, detail="LLM produced no result")

    data = result.model_dump()
    logger.info("✅ {active_model} generation completed")
    logger.debug(f"{active_model} keys: {list(data.keys())}")

    return data

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /analysis/run ({active_model})")
    raise HTTPException(status_code=500, detail="Internal server error")
