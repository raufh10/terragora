from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException

from services.llm import OpenAIResponse
from services.schemas import SubmissionCategory, PostCategory

from logger import start_logger
logger = start_logger()
router = APIRouter()

@router.post("/analysis/run")
async def run_analysis(
  payload: Optional[Dict[str, Any]] = Body(None),
):
  logger.info("📥 Starting /analysis/run (SubmissionCategory)")
  try:
    payload = payload or {}
    system_prompt = str(payload.get("system_prompt", "")).strip()
    user_prompt = str(payload.get("user_prompt", "")).strip()

    if not system_prompt:
      logger.warning("⚠️ Missing system_prompt for SubmissionCategory generation")
    if not user_prompt:
      logger.warning("⚠️ Missing user_prompt for SubmissionCategory generation")

    logger.debug(f"Prompt lengths | system={len(system_prompt)} user={len(user_prompt)}")

    llm = OpenAIResponse()
    result = llm.generate_structured_response(
      logger,
      system_prompt,
      user_prompt,
      response_format=SubmissionCategory
    )

    if not result:
      logger.error("⚠️ LLM returned no structured result (SubmissionCategory)")
      raise HTTPException(status_code=502, detail="LLM produced no result")

    data = result.model_dump()
    logger.info("✅ SubmissionCategory generation completed")
    logger.debug(f"SubmissionCategory keys: {list(data.keys())}")

    return data

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /analysis/run (SubmissionCategory)")
    raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/analysis/test")
async def test_analysis(
  payload: Optional[Dict[str, Any]] = Body(None),
):
  logger.info("📥 Starting /analysis/run (PostCategory)")
  try:
    payload = payload or {}
    system_prompt = str(payload.get("system_prompt", "")).strip()
    user_prompt = str(payload.get("user_prompt", "")).strip()

    if not system_prompt:
      logger.warning("⚠️ Missing system_prompt for PostCategory generation")
    if not user_prompt:
      logger.warning("⚠️ Missing user_prompt for PostCategory generation")

    logger.debug(f"Prompt lengths | system={len(system_prompt)} user={len(user_prompt)}")

    llm = OpenAIResponse()
    result = llm.generate_structured_response(
      logger,
      system_prompt,
      user_prompt,
      response_format=PostCategory
    )

    if not result:
      logger.error("⚠️ LLM returned no structured result (PostCategory)")
      raise HTTPException(status_code=502, detail="LLM produced no result")

    data = result.model_dump()
    logger.info("✅ PostCategory generation completed")
    logger.debug(f"PostCategory keys: {list(data.keys())}")

    return data

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /analysis/run (PostCategory)")
    raise HTTPException(status_code=500, detail="Internal server error")
