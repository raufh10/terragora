from typing import Optional, Dict, Any
from fastapi import APIRouter, Body, HTTPException, Depends
from supabase import Client

from services.database import db, agendas as agendas_svc

from logger import start_logger
logger = start_logger()
router = APIRouter()

@router.post("/agendas/{agenda_id}")
async def agendas_edit(
  agenda_id: int,
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info(f"📥 /agendas/{agenda_id} (edit)")
  try:
    payload = payload or {}

    has_name = "name" in payload
    has_subreddit = "subreddit" in payload
    has_data = "data" in payload

    if not (has_name or has_subreddit or has_data):
      raise HTTPException(
        status_code=400,
        detail="At least one of 'name', 'subreddit', or 'data' must be provided"
      )

    updated_fields: Dict[str, Any] = {}

    if has_name:
      new_name = str(payload.get("name", "")).strip()
      if not new_name:
        raise HTTPException(status_code=400, detail="name cannot be empty")
      logger.info(f"✏️ Updating agenda name | id={agenda_id}")
      resp = await agendas_svc.edit_name(supabase, logger, agenda_id, new_name)
      if not resp.get("ok"):
        raise HTTPException(status_code=502, detail=resp.get("error", "edit_name failed"))
      updated_fields["name"] = resp.get("data")

    if has_subreddit:
      new_subreddit = str(payload.get("subreddit", "")).strip()
      if not new_subreddit:
        raise HTTPException(status_code=400, detail="subreddit cannot be empty")
      logger.info(f"✏️ Updating agenda subreddit | id={agenda_id}")
      resp = await agendas_svc.edit_subreddit(supabase, logger, agenda_id, new_subreddit)
      if not resp.get("ok"):
        raise HTTPException(status_code=502, detail=resp.get("error", "edit_subreddit failed"))
      updated_fields["subreddit"] = resp.get("data")

    if has_data:
      new_data = payload.get("data")
      if not isinstance(new_data, dict):
        raise HTTPException(status_code=400, detail="data must be a JSON object")
      logger.info(f"✏️ Updating agenda data | id={agenda_id}")
      resp = await agendas_svc.edit_data(supabase, logger, agenda_id, new_data)
      if not resp.get("ok"):
        raise HTTPException(status_code=502, detail=resp.get("error", "edit_data failed"))
      updated_fields["data"] = resp.get("data")

    if not updated_fields:
      raise HTTPException(status_code=400, detail="No valid fields to update")

    logger.info(f"✅ Agenda updated | id={agenda_id} fields={list(updated_fields.keys())}")
    return {
      "ok": True,
      "agenda_id": agenda_id,
      "updated_fields": list(updated_fields.keys()),
      "data": updated_fields,
    }

  except HTTPException:
    raise
  except Exception:
    logger.exception(f"💥 Unhandled error in /agendas/{agenda_id} (edit)")
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
