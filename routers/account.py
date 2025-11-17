from typing import Optional, Dict, Any
from fastapi import APIRouter, Body, HTTPException, Depends
from supabase import Client

from services.database import db, account as account_svc
from logger import start_logger

logger = start_logger()
router = APIRouter()

# ------------------------------
# DELETE USER (Admin)
# ------------------------------
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


# ------------------------------
# UPDATE EMAIL (Admin)
# ------------------------------
@router.post("/account/admin/update-email")
async def account_admin_update_email(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /account/admin/update-email")
  try:
    payload = payload or {}

    user_id = str(payload.get("user_id", "")).strip()
    new_email = str(payload.get("new_email", "")).strip()

    if not user_id:
      raise HTTPException(status_code=400, detail="user_id is required")
    if not new_email:
      raise HTTPException(status_code=400, detail="new_email is required")

    resp = await account_svc.admin_update_user_email(
      supabase=supabase,
      logger=logger,
      user_id=user_id,
      new_email=new_email
    )

    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "admin_update_user_email failed"))

    return resp

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /account/admin/update-email")
    raise HTTPException(status_code=500, detail="Internal server error")


# ------------------------------
# UPDATE PASSWORD (Admin)
# ------------------------------
@router.post("/account/admin/update-password")
async def account_admin_update_password(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /account/admin/update-password")
  try:
    payload = payload or {}

    user_id = str(payload.get("user_id", "")).strip()
    new_password = str(payload.get("new_password", "")).strip()

    if not user_id:
      raise HTTPException(status_code=400, detail="user_id is required")
    if not new_password:
      raise HTTPException(status_code=400, detail="new_password is required")

    resp = await account_svc.admin_update_user_password(
      supabase=supabase,
      logger=logger,
      user_id=user_id,
      new_password=new_password
    )

    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "admin_update_user_password failed"))

    return resp

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /account/admin/update-password")
    raise HTTPException(status_code=500, detail="Internal server error")
