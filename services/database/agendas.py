from supabase import Client
from typing import Optional

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
