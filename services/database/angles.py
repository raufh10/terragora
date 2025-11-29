from supabase import Client
from typing import Optional

async def insert(
  supabase: Client,
  logger,
  data: dict
):

  try:
    response = (
      supabase
      .table("angles")
      .insert(data)
      .execute()
    )

    if response.data:
      return True

  except Exception as e:
    logger.error(f"Exception bulk inserting angles: {e}")
    return False

async def select_labeled(
  supabase: Client,
  logger,
  agenda_id: int
):

  try:
    response = (
      supabase
      .table("angles")
      .select("submission_id")
      .eq("agenda_id", agenda_id)
      .execute()
    )

    if response.data:
      return [item["submission_id"] for item in response.data]
    else:
      return []

  except Exception as e:
    logger.error(f"Exception selecting angles: {e}")
    return []
