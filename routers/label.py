import yaml
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException, Depends

from services.llm import OpenAIResponse
from services.schemas import DiscoverCategory, NBAThreadCategory, RedditReplyIdeas

from supabase import Client
from services.database import db, angles, submissions as submissions_svc

from logger import start_logger
logger = start_logger()
router = APIRouter()

PROMPTS_PATH = "data/prompts.yaml"
def _load_prompts_yaml(logger, path: str = PROMPTS_PATH):
  try:
    with open(path, "r", encoding="utf-8") as f:
      data = yaml.safe_load(f)
  except Exception as e:
    logger.exception(f"❌ Unable to read or parse YAML at {path}")
    raise RuntimeError(f"Failed to read/parse prompts YAML: {e}") from e

  if not isinstance(data, dict):
    raise ValueError(f"Invalid YAML structure in {path}: expected a mapping at top-level")

  block = data.get("discover_category")
  if not isinstance(block, dict):
    raise ValueError("Missing required key 'submission_category' (mapping) in prompts YAML")

  system_prompt = block.get("system_prompt")
  user_prompt = block.get("user_prompt")

  if not isinstance(system_prompt, str) or not system_prompt.strip():
    raise ValueError("'submission_category.system_prompt' must be a non-empty string")

  if not isinstance(user_prompt, str) or not user_prompt.strip():
    raise ValueError("'submission_category.user_prompt' must be a non-empty string")

  return system_prompt.strip(), user_prompt.strip()

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
    final_data = {
      "list": [item["subcategory"] for item in data],
      "data": data
    }

    logger.info("✅ {active_model} generation completed")
    logger.debug(f"{active_model} keys: {list(data.keys())}")

    return final_data

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /analysis/run ({active_model})")
    raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/suggest/run")
async def run_suggest(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client)
):

  active_model = RedditReplyIdeas
  logger.info("📥 Starting /suggest/run ({active_model})")

  try:
    payload = payload or {}
    user_id = payload.get("user_id", "")
    submission_id = payload.get("submission_id", None)

    if not user_id or not submission_id:
      raise HTTPException(status_code=400, detail="ids is required")

    data = submissions_svc.simple_select(supabase, logger, submission_data)
    if not data:
      logger.warning("⚠️ Missing data")
      raise HTTPException(status_code=502, detail="No data found in database")

    subreddit = data.get("subreddit", "")
    title = data.get("title", "")
    selftext = data.get("selftext", "")
    link_flair_text = data.get("link_flair_text", "")

    system_prompt, user_prompt_tpl = _load_prompts_yaml(logger, PROMPTS_PATH)
    user_prompt = user_prompt_tpl.format(
      subreddit=agenda_subreddit,
      link_flair_text=link_flair_text,
      title=title,
      selftext=selftext,
    ).strip()

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

    data_result = result.model_dump()
    logger.info("✅ {active_model} generation completed")
    logger.debug(f"{active_model} keys: {list(data.keys())}")

    insert_payload = {
      "user_id": user_id,
      "submission_id": submission_id,
      "data": data_result
    }

    row = await angles.insert(supabase, logger, insert_payload)
    if not row:
      raise HTTPException(status_code=502, detail="Failed to insert angle")

    return {
      "ok": True,
      "data": row,
    }

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /analysis/run ({active_model})")
    raise HTTPException(status_code=500, detail="Internal server error")
