from typing import Optional, Dict, Any
from fastapi import APIRouter, Body, HTTPException, Depends
from supabase import Client

from services.database import db, profiles as profiles_svc

from logger import start_logger
logger = start_logger()
router = APIRouter()

@router.post("/profiles/is_permitted")
async def profiles_edit_is_permitted(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /profiles/is_permitted")
  try:
    payload = payload or {}

    user_id = payload.get("user_id")
    if not isinstance(user_id, str):
      raise HTTPException(status_code=400, detail="user_id must be a str")

    is_permitted = payload.get("is_permitted", None)
    if is_permitted is None:
      raise HTTPException(status_code=400, detail="is_permitted is required")

    resp = await profiles_svc.edit_is_permitted(supabase, logger, user_id, bool(is_permitted))
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "edit_is_permitted failed"))
    return resp
  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /profiles/is_permitted")
    raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/profiles/edit_user_name")
async def profiles_edit_user_name(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /profiles/edit_user_name")
  try:
    payload = payload or {}

    user_id = payload.get("user_id")
    if not isinstance(user_id, str):
      raise HTTPException(status_code=400, detail="user_id must be a str")

    new_user_name = str(payload.get("user_name", "")).strip()
    if not new_user_name:
      raise HTTPException(status_code=400, detail="user_name cannot be empty")

    resp = await profiles_svc.edit_user_name(supabase, logger, user_id, new_user_name)
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "edit_user_name failed"))

    return {
      "ok": True,
      "user_id": user_id,
      "updated_fields": ["user_name"],
      "data": resp.get("data"),
    }

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /profiles/edit_user_name")
    raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/profiles/create")
async def profiles_create(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /profiles/create")
  try:
    payload = payload or {}

    user_id = str(payload.get("user_id", "")).strip()
    data_field = payload.get("data")

    if not user_id:
      raise HTTPException(status_code=400, detail="user_id is required")
    if not isinstance(data_field, dict):
      raise HTTPException(status_code=400, detail="data must be a JSON object")

    insert_payload = {
      "user_id": user_id,
      "data": data_field
    }

    row = await profiles_svc.insert(supabase, logger, insert_payload)
    if not row:
      raise HTTPException(status_code=502, detail="Failed to insert profile")

    return {
      "ok": True,
      "data": row,
    }

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /profiles/create")
    raise HTTPException(status_code=500, detail="Internal server error")
