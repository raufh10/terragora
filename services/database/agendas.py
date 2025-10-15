from supabase import Client
from typing import Optional

async def select(
  supabase: Client,
  logger,
  id: int
):

  try:
    response = (
      supabase
      .table("agendas")
      .select("*")
      .eq("id", id)
      .execute()
    )

    if response.data:
      return response.data[0]

  except Exception as e:
    logger.error(f"Exception selecting agenda: {e}")
    return {}