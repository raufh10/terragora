from typing import Optional, Dict, Any
from fastapi import APIRouter, Body, HTTPException, Depends
from supabase import Client

from services.database import db
from services.database import account as account_svc

from logger import start_logger
logger = start_logger()
router = APIRouter()


@router.post("/account/signup")
async def account_signup(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /account/signup")
  try:
    payload = payload or {}
    email = str(payload.get("email", "")).strip()
    password = str(payload.get("password", "")).strip()

    if not email or not password:
      raise HTTPException(status_code=400, detail="email and password are required")

    resp = await account_svc.sign_up(supabase, logger, email, password)
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "sign_up failed"))
    return resp

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /account/signup")
    raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/account/signin")
async def account_signin(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /account/signin")
  try:
    payload = payload or {}
    email = str(payload.get("email", "")).strip()
    password = str(payload.get("password", "")).strip()

    if not email or not password:
      raise HTTPException(status_code=400, detail="email and password are required")

    resp = await account_svc.sign_in(supabase, logger, email, password)
    if not resp.get("ok"):
      raise HTTPException(status_code=401, detail=resp.get("error", "sign_in failed"))
    return resp

  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /account/signin")
    raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/account/signout")
async def account_signout(
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /account/signout")
  try:
    resp = await account_svc.sign_out(supabase, logger)
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "sign_out failed"))
    return resp
  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /account/signout")
    raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/account/password/reset")
async def account_reset_password(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /account/password/reset")
  try:
    payload = payload or {}
    email = str(payload.get("email", "")).strip()
    redirect_to = payload.get("redirect_to")
    if not email:
      raise HTTPException(status_code=400, detail="email is required")

    resp = await account_svc.reset_password_for_email(supabase, logger, email, redirect_to)
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "reset_password_for_email failed"))
    return resp
  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /account/password/reset")
    raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/account/session")
async def account_get_session(
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /account/session")
  try:
    resp = await account_svc.get_session(supabase, logger)
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "get_session failed"))
    return resp
  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /account/session")
    raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/account/session/refresh")
async def account_refresh_session(
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /account/session/refresh")
  try:
    resp = await account_svc.refresh_session(supabase, logger)
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "refresh_session failed"))
    return resp
  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /account/session/refresh")
    raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/account/update/email")
async def account_update_email(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /account/update/email")
  try:
    payload = payload or {}
    new_email = str(payload.get("email", "")).strip()
    if not new_email:
      raise HTTPException(status_code=400, detail="email is required")

    resp = await account_svc.update_user_email(supabase, logger, new_email)
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "update_user_email failed"))
    return resp
  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /account/update/email")
    raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/account/update/password")
async def account_update_password(
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info("📥 /account/update/password")
  try:
    payload = payload or {}
    new_password = str(payload.get("password", "")).strip()
    if not new_password:
      raise HTTPException(status_code=400, detail="password is required")

    resp = await account_svc.update_user_password(supabase, logger, new_password)
    if not resp.get("ok"):
      raise HTTPException(status_code=502, detail=resp.get("error", "update_user_password failed"))
    return resp
  except HTTPException:
    raise
  except Exception:
    logger.exception("💥 Unhandled error in /account/update/password")
    raise HTTPException(status_code=500, detail="Internal server error")


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
