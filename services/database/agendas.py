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

# ---------- Agendas router ----------
async def select(
  supabase: Client,
  logger,
  profile_id: int
):
  try:

    response = (
      supabase.table("agendas")
      .select("id, data, profiles(name, is_permitted)")
      .eq("profile_id", profile_id)
      .execute()
    )

    if response.data:
      return response.data[0]
    else:
      return None

  except Exception as e:
    logger.error(f"Failed to fetch agenda based on id: {str(e)}")
    return None

async def insert(
  supabase: Client,
  logger,
  data: dict
):

  try:
    response = (
      supabase
      .table("agendas")
      .insert(data)
      .execute()
    )

    if response.data:
      return response.data[0]

  except Exception as e:
    logger.error(f"Exception inserting agendas: {e}")
    return {}

async def edit_data(
  supabase: Client,
  logger,
  agenda_id: int,
  new_data: dict
) -> Dict[str, Any]:
  if not agenda_id or not isinstance(new_data, dict):
    return _fail(logger, "edit_data requires valid agenda_id and new_data dict")

  try:
    response = (
      supabase
      .table("agendas")
      .update({"data": new_data})
      .eq("id", agenda_id)
      .execute()
    )

    if response.data:
      logger.info(f"✅ Updated agenda data | id={agenda_id}")
      return _ok(response.data)
    return _fail(logger, f"⚠️ No rows updated for id={agenda_id}")

  except Exception as e:
    return _fail(logger, f"edit_data failed for id={agenda_id}", e)

# ---------- Misc ----------
async def select_subreddit(
  supabase: Client,
  logger,
  id: int
):
  try:

    response = (
      supabase.table("agendas")
      .select("data")
      .eq("id", id)
      .execute()
    )

    if response.data:
      return response.data[0]["subreddit"], response.data[0]["type"]
    else:
      return None, None

  except Exception as e:
    logger.error(f"Failed to fetch agenda subreddit and type based on id: {str(e)}")
    return None, None

async def select_user_id(
  supabase: Client,
  logger,
  agenda_id: int
):
  try:

    response = (
      supabase.table("agendas")
      .select("user_id")
      .eq("id", agenda_id)
      .execute()
    )

    if response.data:
      return response.data[0]["user_id"]
    else:
      return None

  except Exception as e:
    logger.error(f"Failed to fetch user_id based on agenda id: {str(e)}")
    return None
