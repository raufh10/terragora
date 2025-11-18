from typing import Optional, Dict, Any
from fastapi import APIRouter, Body, HTTPException, Depends
from supabase import Client

from services.database import db, agendas as agendas_svc

from logger import start_logger
logger = start_logger()
router = APIRouter()

@router.post("/agendas/edit")
async def agendas_edit(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /agendas/edit")
  try:
    payload = payload or {}

    agenda_id = payload.get("agenda_id")
    if not isinstance(agenda_id, int) or agenda_id <= 0:
      raise HTTPException(status_code=400, detail="agenda_id must be a positive integer")

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
    logger.exception("💥 Unhandled error in /agendas/edit")
    raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/agendas/is_permitted")
async def agendas_edit_is_permitted(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /agendas/is_permitted")
  try:
    payload = payload or {}

    agenda_id = payload.get("agenda_id")
    if not isinstance(agenda_id, int) or agenda_id <= 0:
      raise HTTPException(status_code=400, detail="agenda_id must be a positive integer")

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
    logger.exception("💥 Unhandled error in /agendas/is_permitted")
    raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/agendas/select")
async def agendas_select_by_user(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /agendas/select (by user_id)")
  try:
    payload = payload or {}

    user_id = str(payload.get("user_id", "")).strip()
    if not user_id:
      raise HTTPException(status_code=400, detail="user_id is required")

    row = await agendas_svc.select(supabase, logger, user_id)
    if row is None:
      return {
        "ok": False,
        "data": None,
        "error": f"No agenda found for user_id={user_id}"
      }

    return {
      "ok": True,
      "data": row
    }

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /agendas/select (by user_id)")
    raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/agendas/create")
async def agendas_create(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /agendas/create")
  try:
    payload = payload or {}

    subreddit = str(payload.get("subreddit", "")).strip()
    user_id = str(payload.get("user_id", "")).strip()
    name = str(payload.get("name", "")).strip()
    user_name = str(payload.get("user_name", "")).strip()
    data_field = payload.get("data")

    if not subreddit:
      raise HTTPException(status_code=400, detail="subreddit is required")
    if not user_id:
      raise HTTPException(status_code=400, detail="user_id is required")
    if not name:
      raise HTTPException(status_code=400, detail="name is required")
    if not user_name:
      raise HTTPException(status_code=400, detail="user_name is required")
    if not isinstance(data_field, dict):
      raise HTTPException(status_code=400, detail="data must be a JSON object")

    insert_payload = {
      "subreddit": subreddit,
      "user_id": user_id,
      "name": name,
      "user_name": user_name,
      "data": data_field,
    }

    row = await agendas_svc.insert(supabase, logger, insert_payload)
    if not row:
      raise HTTPException(status_code=502, detail="Failed to insert agenda")

    return {
      "ok": True,
      "data": row,
    }

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /agendas/create")
    raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/agendas/edit_user_name")
async def agendas_edit_user_name(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /agendas/edit_user_name")
  try:
    payload = payload or {}

    agenda_id = payload.get("agenda_id")
    if not isinstance(agenda_id, int) or agenda_id <= 0:
      raise HTTPException(status_code=400, detail="agenda_id must be a positive integer")

    new_user_name = str(payload.get("user_name", "")).strip()
    if not new_user_name:
      raise HTTPException(status_code=400, detail="user_name cannot be empty")

    resp = await agendas_svc.edit_user_name(supabase, logger, agenda_id, new_user_name)
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "edit_user_name failed"))

    return {
      "ok": True,
      "agenda_id": agenda_id,
      "updated_fields": ["user_name"],
      "data": resp.get("data"),
    }

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /agendas/edit_user_name")
    raise HTTPException(status_code=500, detail="Internal server error")

