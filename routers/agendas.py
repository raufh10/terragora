from typing import Optional, Dict, Any
from fastapi import APIRouter, Body, HTTPException, Depends
from supabase import Client

from services.database import db
from services.database import agendas as agendas_svc

from logger import start_logger
logger = start_logger()
router = APIRouter()


@router.post("/agendas/{agenda_id}/name")
async def agendas_edit_name(
  agenda_id: int,
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info(f"📥 /agendas/{agenda_id}/name")
  try:
    payload = payload or {}
    new_name = str(payload.get("name", "")).strip()
    if not new_name:
      raise HTTPException(status_code=400, detail="name is required")

    resp = await agendas_svc.edit_name(supabase, logger, agenda_id, new_name)
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "edit_name failed"))
    return resp
  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /agendas/{agenda_id}/name")
    raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/agendas/{agenda_id}/subreddit")
async def agendas_edit_subreddit(
  agenda_id: int,
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info(f"📥 /agendas/{agenda_id}/subreddit")
  try:
    payload = payload or {}
    new_subreddit = str(payload.get("subreddit", "")).strip()
    if not new_subreddit:
      raise HTTPException(status_code=400, detail="subreddit is required")

    resp = await agendas_svc.edit_subreddit(supabase, logger, agenda_id, new_subreddit)
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "edit_subreddit failed"))
    return resp
  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /agendas/{agenda_id}/subreddit")
    raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/agendas/{agenda_id}/data")
async def agendas_edit_data(
  agenda_id: int,
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info(f"📥 /agendas/{agenda_id}/data")
  try:
    payload = payload or {}
    new_data = payload.get("data")
    if not isinstance(new_data, dict):
      raise HTTPException(status_code=400, detail="data must be a JSON object")

    resp = await agendas_svc.edit_data(supabase, logger, agenda_id, new_data)
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "edit_data failed"))
    return resp
  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /agendas/{agenda_id}/data")
    raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/agendas/{agenda_id}/is_permitted")
async def agendas_edit_is_permitted(
  agenda_id: int,
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info(f"📥 /agendas/{agenda_id}/is_permitted")
  try:
    payload = payload or {}
    # accept truthy/falsy forms and cast to bool
    is_permitted = payload.get("is_permitted", None)
    if is_permitted is None:
      raise HTTPException(status_code=400, detail="is_permitted is required")

    resp = await agendas_svc.edit_is_permitted(supabase, logger, agenda_id, bool(is_permitted))
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "edit_is_permitted failed"))
    return resp
  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /agendas/{agenda_id}/is_permitted")
    raise HTTPException(status_code=500, detail="Internal server error")
