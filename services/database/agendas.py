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
async def edit_name(
  supabase: Client,
  logger,
  agenda_id: int,
  new_name: str
) -> Dict[str, Any]:
  """Update the 'name' field of an agenda."""
  if not agenda_id or not new_name:
    return _fail(logger, "edit_name requires agenda_id and new_name")

  try:
    response = (
      supabase
      .table("agendas")
      .update({"name": new_name})
      .eq("id", agenda_id)
      .execute()
    )

    if response.data:
      logger.info(f"✅ Updated agenda name | id={agenda_id}")
      return _ok(response.data)
    return _fail(logger, f"⚠️ No rows updated for id={agenda_id}")

  except Exception as e:
    return _fail(logger, f"edit_name failed for id={agenda_id}", e)

async def edit_user_name(
  supabase: Client,
  logger,
  agenda_id: int,
  new_name: str
) -> Dict[str, Any]:
  """Update the 'user_name' field of an agenda."""
  if not agenda_id or not new_name:
    return _fail(logger, "edit_name requires agenda_id and new_name")

  try:
    response = (
      supabase
      .table("agendas")
      .update({"user_name": new_name})
      .eq("id", agenda_id)
      .execute()
    )

    if response.data:
      logger.info(f"✅ Updated agenda user_name | id={agenda_id}")
      return _ok(response.data)
    return _fail(logger, f"⚠️ No rows updated for id={agenda_id}")

  except Exception as e:
    return _fail(logger, f"edit_name failed for id={agenda_id}", e)

# ---------- Update column: subreddit ----------
async def edit_subreddit(
  supabase: Client,
  logger,
  agenda_id: int,
  new_subreddit: str
) -> Dict[str, Any]:
  """Update the 'subreddit' field of an agenda."""
  if not agenda_id or not new_subreddit:
    return _fail(logger, "edit_subreddit requires agenda_id and new_subreddit")

  try:
    response = (
      supabase
      .table("agendas")
      .update({"subreddit": new_subreddit})
      .eq("id", agenda_id)
      .execute()
    )

    if response.data:
      logger.info(f"✅ Updated agenda subreddit | id={agenda_id}")
      return _ok(response.data)
    return _fail(logger, f"⚠️ No rows updated for id={agenda_id}")

  except Exception as e:
    return _fail(logger, f"edit_subreddit failed for id={agenda_id}", e)

# ---------- Update column: data ----------
async def edit_data(
  supabase: Client,
  logger,
  agenda_id: int,
  new_data: dict
) -> Dict[str, Any]:
  """Update the 'data' JSON field of an agenda."""
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

# ---------- Update column: is_permitted ----------
async def edit_is_permitted(
  supabase: Client,
  logger,
  agenda_id: int,
  is_permitted: bool
) -> Dict[str, Any]:
  """Update the 'is_permitted' boolean field of an agenda."""
  if agenda_id is None or is_permitted is None:
    return _fail(logger, "edit_is_permitted requires agenda_id and is_permitted")

  try:
    response = (
      supabase
      .table("agendas")
      .update({"is_permitted": bool(is_permitted)})
      .eq("id", agenda_id)
      .execute()
    )

    if response.data:
      logger.info(f"✅ Updated agenda permission | id={agenda_id}")
      return _ok(response.data)
    return _fail(logger, f"⚠️ No rows updated for id={agenda_id}")

  except Exception as e:
    return _fail(logger, f"edit_is_permitted failed for id={agenda_id}", e)

async def select(
  supabase: Client,
  logger,
  user_id: str
):
  try:

    response = (
      supabase.table("agendas")
      .select("id, name, user_name, subreddit, data->type, data->location")
      .eq("user_id", user_id)
      .execute()
    )

    if response.data:
      return response.data[0]
    else:
      return None

  except Exception as e:
    logger.error(f"Failed to fetch agenda based on id: {str(e)}")
    return None

async def select_subreddit(
  supabase: Client,
  logger,
  id: int
):
  try:

    response = (
      supabase.table("agendas")
      .select("subreddit, data->type")
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
