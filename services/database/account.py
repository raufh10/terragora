from supabase import Client
from typing import Dict, Any, Optional

# ---------- Helpers ----------
def _ok(data: Any = None) -> Dict[str, Any]:
  return {"ok": True, "data": data}

def _fail(logger, msg: str, exc: Optional[Exception] = None) -> Dict[str, Any]:
  if exc:
    logger.error(f"{msg}: {exc}")
  else:
    logger.error(msg)
  return {"ok": False, "error": msg}

# ---------- Admin: Delete User ----------
async def admin_delete_user(
  supabase: Client,
  logger,
  user_id: str
) -> Dict[str, Any]:
  """
  Delete a user by ID using the Admin API.
  Requires the Supabase client to be initialized with a service role key.
  """
  if not user_id:
    return _fail(logger, "admin_delete_user requires non-empty user_id")

  try:
    resp = supabase.auth.admin.delete_user(user_id)
    return _ok(resp)
  except Exception as e:
    return _fail(logger, f"admin_delete_user failed for user_id={user_id}", e)

# ---------- Admin: Update User Email ----------
async def admin_update_user_email(
  supabase: Client,
  logger,
  user_id: str,
  new_email: str
) -> Dict[str, Any]:
  """
  Update a user's email by ID using the Admin API.
  Requires the Supabase client to be initialized with a service role key.
  """
  if not user_id:
    return _fail(logger, "admin_update_user_email requires non-empty user_id")
  if not new_email:
    return _fail(logger, "admin_update_user_email requires non-empty new_email")

  try:
    resp = supabase.auth.admin.update_user_by_id(
      user_id,
      {
        "email": new_email,
      },
    )
    return _ok(resp)
  except Exception as e:
    return _fail(logger, f"admin_update_user_email failed for user_id={user_id}", e)

# ---------- Admin: Update User Password ----------
async def admin_update_user_password(
  supabase: Client,
  logger,
  user_id: str,
  new_password: str
) -> Dict[str, Any]:
  """
  Update a user's password by ID using the Admin API.
  Requires the Supabase client to be initialized with a service role key.
  """
  if not user_id:
    return _fail(logger, "admin_update_user_password requires non-empty user_id")
  if not new_password:
    return _fail(logger, "admin_update_user_password requires non-empty new_password")

  try:
    resp = supabase.auth.admin.update_user_by_id(
      user_id,
      {
        "password": new_password,
      },
    )
    return _ok(resp)
  except Exception as e:
    return _fail(logger, f"admin_update_user_password failed for user_id={user_id}", e)
