from supabase import Client
from typing import Optional

def explode_agenda_items(items: list[dict]) -> list[dict]:
  return [
    {
      "agenda_id": entry.get("id"),
      "subreddit": key,
      **value
    }
    for entry in items
    if isinstance(entry, dict)
    for key, value in (entry.get("data") or {}).items()
    if isinstance(value, dict)
  ]

async def select(
  supabase: Client,
  logger,
  id: int = None
):

  try:
    query = (
      supabase
      .table("agendas")
      .select("data")
    )

    if id:
      query.eq("id", id)

    response = query.execute()

    if response.data:
      return sorted(set().union(*(d["data"].keys() for d in response.data)))
    else:
      return []

  except Exception as e:
    logger.error(f"Exception selecting agenda: {e}")
    return []

async def select_all(
  supabase: Client,
  logger
):

  try:
    query = (
      supabase
      .table("agendas")
      .select("id, data")
    )
    response = query.execute()

    if response.data:
      return explode_agenda_items(response.data)

    else:
      return []

  except Exception as e:
    logger.error(f"Exception selecting all agenda: {e}")
    return []
