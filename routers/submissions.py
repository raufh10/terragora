from typing import Optional, Dict, Any
from fastapi import APIRouter, Body, HTTPException, Depends
from supabase import Client

from services.database import db, submissions
from logger import start_logger
logger = start_logger()
router = APIRouter()

@router.post("/submissions/{agenda_id}/feed")
async def fetch_submissions(
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
