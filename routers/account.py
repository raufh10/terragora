from typing import Optional, Dict, Any
from fastapi import APIRouter, Body, HTTPException, Depends
from supabase import Client

from services.database import db, account as account_svc

from logger import start_logger
logger = start_logger()
router = APIRouter()

@router.post("/account/admin/delete")
async def account_admin_delete_user(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /account/admin/delete")
  try:
    payload = payload or {}
    user_id = str(payload.get("user_id", "")).strip()
    if not user_id:
      raise HTTPException(status_code=400, detail="user_id is required")

    resp = await account_svc.admin_delete_user(supabase, logger, user_id)
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "admin_delete_user failed"))
    return resp
  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /account/admin/delete")
    raise HTTPException(status_code=500, detail="Internal server error")
