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
      .table("alerts")
      .insert(data)
      .execute()
    )

    if response.data:
      return True

  except Exception as e:
    logger.error(f"Exception bulk inserting alerts: {e}")
    return False

async def select(
  supabase: Client,
  logger
):

  try:
    response = (
      supabase
      .table("alerts")
      .select(
        "id, relevance, message"
        "agendas:agenda_id(type), "
        "submissions:submission_id(subreddit, data)"
      )
      .eq("status", "pending")
      .execute()
    )

    if response.data:
      return response.data

  except Exception as e:
    logger.error(f"Exception selecting agenda: {e}")
    return []

async def update_statuses_success(supabase: Client, logger, inserted_ids) -> bool:
  try:
    response = (
      supabase.table("alerts")
      .update({"status": "success"})
      .in_("id", inserted_ids)
      .execute()
    )
    return bool(response.data)

  except Exception as e:
    logger.error(f"Bulk update failed: {e}")
    return False