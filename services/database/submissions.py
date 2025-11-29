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
      .upsert(
        data,
        on_conflict="reddit_id,subreddit",
      )
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

async def select_to_label(
  supabase: Client,
  logger,
  subreddit: str,
  angles_ids: list
):

  try:
    query = (
      supabase
      .table("submissions")
      .select(
        "id, "
        "data->title, "
        "data->link_flair_text, "
        "data->selftext"
      )
      .eq("subreddit", subreddit)
      .order("data->created_utc", desc="desc")
    )

    if angles_ids:
      query.not_.in_("id", angles_ids)

    response = query.execute()

    if response.data:
      return response.data

  except Exception as e:
    logger.error(f"Exception selecting unlabeled posts: {e}")
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
