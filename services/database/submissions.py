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
      .table("submissions")
      .insert(data)
      .execute()
    )

    if response.data:
      return True

  except Exception as e:
    logger.error(f"Exception bulk inserting submissions: {e}")
    return False

async def select(
  supabase: Client,
  logger,
  subreddit: str
):

  try:
    response = (
      supabase
      .table("submissions")
      .select("*")
      .eq("subreddit", subreddit)
      .execute()
    )

    if response.data:
      return response.data

  except Exception as e:
    logger.error(f"Exception selecting agenda: {e}")
    return []

async def select_reddit_ids(
  supabase: Client,
  logger,
  subreddit: str
):

  try:
    response = (
      supabase
      .table("submissions")
      .select("reddit_id")
      .eq("subreddit", subreddit)
      .execute()
    )

    if response.data:
      return [item["reddit_id"] for item in response.data]
    else:
      return []

  except Exception as e:
    logger.error(f"Exception selecting agenda: {e}")
    return []