from typing import Optional, Dict, Any
from fastapi import APIRouter, Body, HTTPException, Depends
from supabase import Client

from services.database import db, cookies as cookies_svc

from logger import start_logger
logger = start_logger()
router = APIRouter()

@router.post("/cookies/create")
async def cookies_create(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /cookies/create")
  try:
    payload = payload or {}

    token = str(payload.get("token", "")).strip()
    data_field = payload.get("data")

    if not token:
      raise HTTPException(status_code=400, detail="token is required")
    if not isinstance(data_field, dict):
      raise HTTPException(status_code=400, detail="data must be a JSON object")

    insert_payload = {
      "token": token,
      "data": data_field,
    }

    row = await cookies_svc.insert(supabase, logger, insert_payload)
    if not row:
      raise HTTPException(status_code=502, detail="Failed to insert cookie")

    return {
      "ok": True,
      "data": row,
    }

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /cookies/create")
    raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/cookies/select")
async def cookies_select(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /cookies/select")
  try:
    payload = payload or {}

    token = str(payload.get("token", "")).strip()
    if not token:
      raise HTTPException(status_code=400, detail="token is required")

    row = await cookies_svc.select(supabase, logger, token)

    if row is None:
      return {
        "ok": False,
        "data": None,
        "error": f"No cookie found for token={token}"
      }

    return {
      "ok": True,
      "data": row
    }

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /cookies/select")
    raise HTTPException(status_code=500, detail="Internal server error")
