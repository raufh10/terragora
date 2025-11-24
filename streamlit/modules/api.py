import os
import json
import requests
import streamlit as st
from supabase import Client, create_client
from typing import List, Dict, Optional, Tuple, Any

from streamlit_cookies_controller import CookieController
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

def _sync_session_into_cookies(logger, auth_resp):
  """
  Given a Supabase auth response (with `.session` and `.user`),
  extract tokens + user info, update session_state, and
  call cookies_create() using the ajs_anonymous_id cookie.
  """
  if auth_resp is None:
    if logger:
      logger.warning("[AUTH] _sync_session_into_cookies called with auth_resp=None")
    return

  # Supabase auth response typically has .session and .user
  session_obj = getattr(auth_resp, "session", None)
  user_obj = getattr(auth_resp, "user", None)

  if session_obj is None:
    if logger:
      logger.warning("[AUTH] _sync_session_into_cookies: missing session object")
    return

  # --- Extract tokens from session branch ---
  access = getattr(session_obj, "access_token", None)
  refresh = getattr(session_obj, "refresh_token", None)
  expires = getattr(session_obj, "expires_at", None)

  # --- Extract user info from user branch (if present) ---
  user_id = None
  user_email = None
  if user_obj is not None:
    user_id = getattr(user_obj, "id", None)
    user_email = getattr(user_obj, "email", None)

  # Fall back to existing session_state if user info not on response
  if user_id is None:
    user_id = st.session_state.get("user_id")
  if user_email is None:
    user_email = st.session_state.get("user_email")

  # --- Persist into session_state for later use ---
  if access is not None:
    st.session_state["auth_token"] = access
  if refresh is not None:
    st.session_state["refresh_token"] = refresh
  if expires is not None:
    st.session_state["session_expires_at"] = expires
  if user_id is not None:
    st.session_state["user_id"] = user_id
  if user_email is not None:
    st.session_state["user_email"] = user_email

  # --- Read ajs_anonymous_id from cookies snapshot in session_state ---
  cookie_state = st.session_state.get("cookies") or {}
  token = cookie_state.get("ajs_anonymous_id")

  if not token:
    if logger:
      logger.warning("[AUTH] Cannot sync cookies: missing ajs_anonymous_id")
    return

  payload = {
    "user_id": user_id,
    "user_email": user_email,
    "access_token": access,
    "refresh_token": refresh,
    "token_expires_at": expires,
  }

  if logger:
    logger.info(f"[AUTH] Syncing auth response → cookies_create() for token={token}")

  resp = cookies_create(logger, token, payload)

  if logger and not resp.get("ok"):
    logger.warning(f"[AUTH] cookies_create failed during session sync: {resp}")

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

# ---------- Auth: Session (Auto-Sync to backend cookies table) ----------
def get_session(
  supabase: Client,
  logger
) -> Dict[str, Any]:
  """Get the current auth session (if any) and sync into cookies table."""
  try:
    resp = supabase.auth.get_session()
    result = _ok(resp)

    # resp now holds both .session and .user branches
    _sync_session_into_cookies(logger, resp)

    return result
  except Exception as e:
    return _fail(logger, "get_session failed", e)


def refresh_session(
  supabase: Client,
  logger
) -> Dict[str, Any]:
  """Refresh tokens, then sync to cookies table."""
  try:
    resp = supabase.auth.refresh_session()
    result = _ok(resp)

    # resp now holds both .session and .user branches
    _sync_session_into_cookies(logger, resp)

    return result
  except Exception as e:
    return _fail(logger, "refresh_session failed", e)


def set_session_from_tokens(
  supabase: Client,
  logger,
  access_token: str,
  refresh_token: str
) -> Dict[str, Any]:
  """Set the current auth session from existing tokens, then sync."""
  if not access_token or not refresh_token:
    return _fail(logger, "set_session_from_tokens requires non-empty access_token and refresh_token")

  try:
    resp = supabase.auth.set_session(access_token, refresh_token)
    result = _ok(resp)

    # resp now holds both .session and .user branches
    _sync_session_into_cookies(logger, resp)

    return result
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

def edit_agenda_user_name(
  logger,
  agenda_id: int,
  user_name: str
) -> Dict[str, Any]:
  """
  Call backend route POST /agendas/edit_user_name.

  Mirrors FastAPI endpoint:

    @router.post("/agendas/edit_user_name")
  """
  if not isinstance(agenda_id, int) or agenda_id <= 0:
    return _fail(logger, "edit_agenda_user_name requires a positive integer agenda_id")
  if not user_name:
    return _fail(logger, "edit_agenda_user_name requires non-empty user_name")

  payload = {
    "agenda_id": agenda_id,
    "user_name": user_name,
  }

  try:
    resp = requests.post(
      f"{get_backend_api_endpoint()}/agendas/edit_user_name",
      json=payload,
      timeout=15
    )
    if resp.status_code >= 400:
      msg = f"agendas/edit_user_name failed with status {resp.status_code}: {resp.text}"
      return _fail(logger, msg)

    return resp.json()
  except Exception as e:
    return _fail(logger, "edit_agenda_user_name request failed", e)

def create_agenda(
  logger,
  subreddit: str,
  user_id: str,
  name: str,
  user_name: str,
  data: Dict[str, Any]
) -> Dict[str, Any]:
  """
  Call backend route POST /agendas/create.

  Mirrors FastAPI endpoint:

    @router.post("/agendas/create")
  """
  if not subreddit:
    return _fail(logger, "create_agenda requires non-empty subreddit")
  if not user_id:
    return _fail(logger, "create_agenda requires non-empty user_id")
  if not name:
    return _fail(logger, "create_agenda requires non-empty name")
  if not user_name:
    return _fail(logger, "create_agenda requires non-empty user_name")
  if not isinstance(data, dict):
    return _fail(logger, "create_agenda requires data to be a JSON-serializable dict")

  payload = {
    "subreddit": subreddit,
    "user_id": user_id,
    "name": name,
    "user_name": user_name,
    "data": data,
  }

  try:
    resp = requests.post(
      f"{get_backend_api_endpoint()}/agendas/create",
      json=payload,
      timeout=15
    )
    if resp.status_code >= 400:
      msg = f"agendas/create failed with status {resp.status_code}: {resp.text}"
      return _fail(logger, msg)

    return resp.json()
  except Exception as e:
    return _fail(logger, "create_agenda request failed", e)

# ---------- Dashboard: Submissions feed via BACKEND_API ----------
def fetch_submissions_feed(
  logger,
  agenda_id: int,
  page: int = 1,
  per_page: int = 10,
  sort: str = "default",
  keyword: Optional[str] = None,
  category: Optional[str] = None,
) -> Dict[str, Any]:
  """
  Call backend route POST /submissions/{agenda_id}/feed.

  Mirrors FastAPI endpoint:

    @router.post("/submissions/{agenda_id}/feed")

  Payload supports:
    - page: int
    - per_page: int
    - sort: "default" | "num_comments" | "scores"
    - keyword: Optional[str]
    - category: Optional[str]
  """
  if not isinstance(agenda_id, int) or agenda_id <= 0:
    return _fail(logger, "fetch_submissions_feed requires a positive integer agenda_id")

  payload: Dict[str, Any] = {
    "page": page,
    "per_page": per_page,
    "sort": sort,
    "keyword": keyword,
    "category": category,
  }

  try:
    resp = requests.post(
      f"{get_backend_api_endpoint()}/submissions/{agenda_id}/feed",
      json=payload,
      timeout=15,
    )
    if resp.status_code >= 400:
      msg = f"submissions/{agenda_id}/feed failed with status {resp.status_code}: {resp.text}"
      return _fail(logger, msg)

    return resp.json()
  except Exception as e:
    return _fail(logger, "fetch_submissions_feed request failed", e)

# ---------- Cookies: via BACKEND_API ----------
def cookies_create(
  logger,
  token: str,
  data: Dict[str, Any]
) -> Dict[str, Any]:
  """
  Call backend route POST /cookies/create.

  Mirrors FastAPI endpoint:

    @router.post("/cookies/create")
  """
  if not token:
    return _fail(logger, "cookies_create requires non-empty token")
  if not isinstance(data, dict):
    return _fail(logger, "cookies_create requires data to be a JSON-serializable dict")

  payload = {
    "token": token,
    "data": data,
  }

  try:
    resp = requests.post(
      f"{get_backend_api_endpoint()}/cookies/create",
      json=payload,
      timeout=15
    )
    if resp.status_code >= 400:
      msg = f"cookies/create failed with status {resp.status_code}: {resp.text}"
      return _fail(logger, msg)

    return resp.json()
  except Exception as e:
    return _fail(logger, "cookies_create request failed", e)

def cookies_select(
  logger,
  token: str
) -> Dict[str, Any]:
  """
  Call backend route POST /cookies/select.

  Mirrors FastAPI endpoint:

    @router.post("/cookies/select")
  """
  if not token:
    return _fail(logger, "cookies_select requires non-empty token")

  payload = {"token": token}

  try:
    resp = requests.post(
      f"{get_backend_api_endpoint()}/cookies/select",
      json=payload,
      timeout=15
    )
    if resp.status_code >= 400:
      msg = f"cookies/select failed with status {resp.status_code}: {resp.text}"
      return _fail(logger, msg)

    return resp.json()
  except Exception as e:
    return _fail(logger, "cookies_select request failed", e)

def cookies_delete(
  logger,
  token: str
) -> Dict[str, Any]:
  """
  Call backend route POST /cookies/delete.
  If deletion is successful, also remove the browser cookie.
  """
  if not token:
    return _fail(logger, "cookies_delete requires non-empty token")

  payload = {"token": token}

  try:
    resp = requests.post(
      f"{get_backend_api_endpoint()}/cookies/delete",
      json=payload,
      timeout=15
    )

    if resp.status_code >= 400:
      msg = f"cookies/delete failed with status {resp.status_code}: {resp.text}"
      return _fail(logger, msg)

    result = resp.json()
    if result.get("ok"):
      try:
        controller = CookieController()
        controller.remove("ajs_anonymous_id")

        if logger:
          logger.info(
            f"[COOKIES] Successfully deleted backend cookie and browser cookie "
            f"for token={token}"
          )
      except Exception as ce:
        if logger:
          logger.warning(f"[COOKIES] Backend cookie deleted but browser cookie removal failed: {ce}")

    return result

  except Exception as e:
    return _fail(logger, "cookies_delete request failed", e)

# ---------- Account Admin: via BACKEND_API ----------
def admin_delete_user(
  logger,
  user_id: str
) -> Dict[str, Any]:
  """
  Call backend route POST /account/admin/delete.
  If successful, also delete the related cookies (backend + browser)
  via cookies_delete().
  """
  if not user_id:
    return _fail(logger, "admin_delete_user requires non-empty user_id")

  payload = {"user_id": user_id}

  try:
    resp = requests.post(
      f"{get_backend_api_endpoint()}/account/admin/delete",
      json=payload,
      timeout=15
    )
    if resp.status_code >= 400:
      msg = f"account/admin/delete failed with status {resp.status_code}: {resp.text}"
      return _fail(logger, msg)

    result = resp.json()

    # If account deletion succeeded, attempt to delete cookies as well
    if result.get("ok"):
      try:
        # Expect ajs_anonymous_id to be stored in session_state["cookies"]
        cookie_state = st.session_state.get("cookies") or {}
        token = cookie_state.get("ajs_anonymous_id")

        if token:
          cookies_delete(logger, token)
        elif logger:
          logger.warning(
            "[ACCOUNT] User deleted but no ajs_anonymous_id token found; "
            "skipping cookies_delete()"
          )
      except Exception as ce:
        if logger:
          logger.warning(
            f"[ACCOUNT] User deleted but cookies_delete() raised an error: {ce}"
          )

    return result

  except Exception as e:
    return _fail(logger, "admin_delete_user request failed", e)

def admin_update_user_email(
  logger,
  user_id: str,
  new_email: str,
  supabase: Optional[Client] = None
) -> Dict[str, Any]:
  """
  Update user email via backend API with automatic token refresh + retry.
  """
  if not user_id:
    return _fail(logger, "admin_update_user_email requires non-empty user_id")
  if not new_email:
    return _fail(logger, "admin_update_user_email requires non-empty new_email")

  payload = {
    "user_id": user_id,
    "new_email": new_email,
  }

  # --- Internal helper: performs the actual HTTP call ---
  def _do_request():
    try:
      resp = requests.post(
        f"{get_backend_api_endpoint()}/account/admin/update-email",
        json=payload,
        timeout=15
      )
      if resp.status_code >= 400:
        msg = f"account/admin/update-email failed with status {resp.status_code}: {resp.text}"
        return _fail(logger, msg)
      return resp.json()
    except Exception as e:
      return _fail(logger, "admin_update_user_email request failed", e)

  # --- First attempt ---
  result = _do_request()

  if result.get("ok"):
    return result

  # ----------------------------------------------------
  # If request FAILS → try refresh session automatically
  # ----------------------------------------------------
  if logger:
    logger.warning("[AUTH] Email update failed — attempting refresh_session()")

  if not supabase:
    return result  # cannot refresh without supabase client

  # 1) Try refresh_session()
  refresh_res = refresh_session(supabase, logger)
  if refresh_res.get("ok"):
    if logger:
      logger.info("[AUTH] refresh_session() succeeded — retrying email update")
    retry_res = _do_request()
    if retry_res.get("ok"):
      return retry_res

  # 2) If refresh_session failed, try set_session_from_tokens()
  access = st.session_state.get("auth_token")
  refresh = st.session_state.get("refresh_token")

  if access and refresh:
    if logger:
      logger.info("[AUTH] refresh_session failed — trying set_session_from_tokens()")

    set_res = set_session_from_tokens(supabase, logger, access, refresh)

    if set_res.get("ok"):
      retry2 = _do_request()
      return retry2

  # If all recovery attempts fail → return original failure
  return result

def admin_update_user_password(
  logger,
  user_id: str,
  new_password: str
) -> Dict[str, Any]:
  """
  Call backend route POST /account/admin/update-password.
  """
  if not user_id:
    return _fail(logger, "admin_update_user_password requires non-empty user_id")
  if not new_password:
    return _fail(logger, "admin_update_user_password requires non-empty new_password")

  payload = {
    "user_id": user_id,
    "new_password": new_password,
  }

  try:
    resp = requests.post(
      f"{get_backend_api_endpoint()}/account/admin/update-password",
      json=payload,
      timeout=15
    )
    if resp.status_code >= 400:
      msg = f"account/admin/update-password failed with status {resp.status_code}: {resp.text}"
      return _fail(logger, msg)

    return resp.json()
  except Exception as e:
    return _fail(logger, "admin_update_user_password request failed", e)

# ---------- Angles: via BACKEND_API ----------
def run_suggest(
  logger,
  user_id: str,
  submission_id: int
) -> Dict[str, Any]:
  """
  Call backend route POST /suggest/run.

  Payload:
    - user_id
    - submission_id
  """
  if not user_id:
    return _fail(logger, "run_suggest requires non-empty user_id")
  if not submission_id:
    return _fail(logger, "run_suggest requires non-empty submission_id")

  payload = {
    "user_id": user_id,
    "submission_id": submission_id,
  }

  try:
    resp = requests.post(
      f"{get_backend_api_endpoint()}/suggest/run",
      json=payload,
      timeout=120
    )
    if resp.status_code >= 400:
      msg = f"suggest/run failed with status {resp.status_code}: {resp.text}"
      return _fail(logger, msg)

    return resp.json()

  except Exception as e:
    return _fail(logger, "run_suggest request failed", e)
