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
      .select("*")
    )

    if id:
      query.eq("id", id)

    response = query.execute()

    if id:
      if response.data:
        return response.data[0]
    else:
      return response.data

  except Exception as e:
    logger.error(f"Exception selecting agenda: {e}")
    return []
