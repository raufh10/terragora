import os
import json
import requests
import streamlit as st
from supabase import Client, create_client
from typing import List, Dict, Optional, Tuple, Any
from modules.config import (
  get_backend_api_endpoint,
  get_supabase_url,
  get_supabase_public_key
)

# ===== Admin =====
def send_telegram_notification(message: str) -> bool:
  try:
    payload = {"message": message}
    response = requests.post(
      f"{get_backend_api_endpoint()}/admin/telegram",
      json=payload,
      timeout=15
    )
    return response.status_code == 200
  except Exception as e:
    return False

# ===== DB Connection =====
@st.cache_resource
def get_supabase_client() -> Client:
  return create_client(
    get_supabase_url(),
    get_supabase_public_key()
  )

# ---------- Helpers ----------
def _ok(data: Any = None) -> Dict[str, Any]:
  return {"ok": True, "data": data}

def _fail(logger, msg: str, exc: Optional[Exception] = None) -> Dict[str, Any]:
  if exc:
    logger.error(f"{msg}: {exc}")
  else:
    logger.error(msg)
  return {"ok": False, "error": msg}

# ---------- Auth: Basic ----------
def sign_up(
  supabase: Client,
  logger,
  email: str,
  password: str
) -> Dict[str, Any]:
  """Create a new user with email/password."""
  if not email or not password:
    return _fail(logger, "sign_up requires non-empty email and password")

  try:
    resp = supabase.auth.sign_up({"email": email, "password": password})
    return _ok(resp)
  except Exception as e:
    return _fail(logger, "sign_up failed", e)

def sign_in(
  supabase: Client,
  logger,
  email: str,
  password: str
) -> Dict[str, Any]:
  """Sign in a user with email/password."""
  if not email or not password:
    return _fail(logger, "sign_in requires non-empty email and password")

  try:
    resp = supabase.auth.sign_in_with_password({"email": email, "password": password})
    return _ok(resp)
  except Exception as e:
    return _fail(logger, "sign_in failed", e)

def sign_out(
  supabase: Client,
  logger
) -> Dict[str, Any]:
  """Sign out the current session."""
  try:
    resp = supabase.auth.sign_out()
    return _ok(resp)
  except Exception as e:
    return _fail(logger, "sign_out failed", e)

# ---------- Auth: Password Reset ----------
def reset_password_for_email(
  supabase: Client,
  logger,
  email: str,
  redirect_to: Optional[str] = None
) -> Dict[str, Any]:
  """Send a password reset email with optional redirect URL."""
  if not email:
    return _fail(logger, "reset_password_for_email requires non-empty email")

  options = {}
  if redirect_to:
    options["redirect_to"] = redirect_to

  try:
    resp = supabase.auth.reset_password_for_email(email, options)
    return _ok(resp)
  except Exception as e:
    return _fail(logger, "reset_password_for_email failed", e)

# ---------- Auth: Session ----------
def get_session(
  supabase: Client,
  logger
) -> Dict[str, Any]:
  """Get the current auth session (if any)."""
  try:
    resp = supabase.auth.get_session()
    return _ok(resp)
  except Exception as e:
    return _fail(logger, "get_session failed", e)

def refresh_session(
  supabase: Client,
  logger
) -> Dict[str, Any]:
  """Refresh the current auth session tokens."""
  try:
    resp = supabase.auth.refresh_session()
    return _ok(resp)
  except Exception as e:
    return _fail(logger, "refresh_session failed", e)

def set_session_from_tokens(
  supabase: Client,
  logger,
  access_token: str,
  refresh_token: str
) -> Dict[str, Any]:
  """Set the current auth session from existing access/refresh tokens."""
  if not access_token or not refresh_token:
    return _fail(logger, "set_session_from_tokens requires non-empty access_token and refresh_token")

  try:
    resp = supabase.auth.set_session(access_token, refresh_token)
    return _ok(resp)
  except Exception as e:
    return _fail(logger, "set_session_from_tokens failed", e)

# ---------- Auth: Update User ----------
def update_user_email(
  supabase: Client,
  logger,
  new_email: str
) -> Dict[str, Any]:
  """Update the current user's email."""
  if not new_email:
    return _fail(logger, "update_user_email requires non-empty new_email")

  try:
    resp = supabase.auth.update_user({"email": new_email})
    return _ok(resp)
  except Exception as e:
    return _fail(logger, "update_user_email failed", e)

def update_user_password(
  supabase: Client,
  logger,
  new_password: str
) -> Dict[str, Any]:
  """Update the current user's password."""
  if not new_password:
    return _fail(logger, "update_user_password requires non-empty new_password")

  try:
    resp = supabase.auth.update_user({"password": new_password})
    return _ok(resp)
  except Exception as e:
    return _fail(logger, "update_user_password failed", e)

# ---------- Agendas: via BACKEND_API ----------
def select_agenda_by_user_id(
  logger,
  user_id: str
) -> Dict[str, Any]:
  """Call backend route POST /agendas/select."""
  if not user_id:
    return _fail(logger, "select_agenda_by_user_id requires non-empty user_id")

  try:
    resp = requests.post(
      f"{get_backend_api_endpoint()}/agendas/select",
      json={"user_id": user_id},
      timeout=15
    )
    if resp.status_code >= 400:
      msg = f"agendas/select failed with status {resp.status_code}: {resp.text}"
      return _fail(logger, msg)

    return resp.json()
  except Exception as e:
    return _fail(logger, "select_agenda_by_user_id request failed", e)

def edit_agenda(
  logger,
  agenda_id: int,
  name: Optional[str] = None,
  subreddit: Optional[str] = None,
  data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
  """
  Call backend route POST /agendas/edit.

  Mirrors the FastAPI endpoint:
    - agenda_id: required, positive int
    - name / subreddit / data: optional fields to update
  """
  if not isinstance(agenda_id, int) or agenda_id <= 0:
    return _fail(logger, "edit_agenda requires a positive integer agenda_id")

  payload: Dict[str, Any] = {"agenda_id": agenda_id}

  if name is not None:
    payload["name"] = name
  if subreddit is not None:
    payload["subreddit"] = subreddit
  if data is not None:
    payload["data"] = data

  # Ensure at least one field besides agenda_id is being updated
  if len(payload) == 1:
    return _fail(logger, "edit_agenda requires at least one of name, subreddit, or data")

  try:
    resp = requests.post(
      f"{get_backend_api_endpoint()}/agendas/edit",
      json=payload,
      timeout=15
    )
    if resp.status_code >= 400:
      msg = f"agendas/edit failed with status {resp.status_code}: {resp.text}"
      return _fail(logger, msg)

    return resp.json()
  except Exception as e:
    return _fail(logger, "edit_agenda request failed", e)
