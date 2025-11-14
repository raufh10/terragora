from supabase import Client
from typing import Dict, Any

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
