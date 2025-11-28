from supabase import Client
from typing import Optional, Dict, Any

# ---------- Helpers ----------
def _ok(data: Any = None) -> Dict[str, Any]:
  return {"ok": True, "data": data}

def _fail(logger, msg: str, exc: Optional[Exception] = None) -> Dict[str, Any]:
  if exc:
    logger.error(f"{msg}: {exc}")
  else:
    logger.error(msg)
  return {"ok": False, "error": msg}

# ---------- Update column: name ----------
async def edit_user_name(
  supabase: Client,
  logger,
  user_id: str,
  new_name: str
) -> Dict[str, Any]:
  if not user_id or not new_name:
    return _fail(logger, "edit_user_name requires user_id and new_name")

  try:
    response = (
      supabase
      .table("profiles")
      .update({"name": new_name})
      .eq("user_id", user_id)
      .execute()
    )

    if response.data:
      logger.info(f"✅ Updated profile name | user_id={user_id}")
      return _ok(response.data)
    return _fail(logger, f"⚠️ No rows updated for user_id={user_id}")

  except Exception as e:
    return _fail(logger, f"edit_user_name failed for user_id={user_id}", e)

# ---------- Update column: is_permitted ----------
async def edit_is_permitted(
  supabase: Client,
  logger,
  user_id: int,
  is_permitted: bool
) -> Dict[str, Any]:
  if user_id is None or is_permitted is None:
    return _fail(logger, "edit_is_permitted requires user_id and is_permitted")

  try:
    response = (
      supabase
      .table("profiles")
      .update({"is_permitted": bool(is_permitted)})
      .eq("user_id", user_id)
      .execute()
    )

    if response.data:
      logger.info(f"✅ Updated profile permission | user_id={user_id}")
      return _ok(response.data)
    return _fail(logger, f"⚠️ No rows updated for user_id={user_id}")

  except Exception as e:
    return _fail(logger, f"edit_is_permitted failed for user_id={user_id}", e)

async def insert(
  supabase: Client,
  logger,
  data: dict
):

  try:
    response = (
      supabase
      .table("profiles")
      .insert(data)
      .execute()
    )

    if response.data:
      return response.data[0]

  except Exception as e:
    logger.error(f"Exception inserting profiles: {e}")
    return {}
