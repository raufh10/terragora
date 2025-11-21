from supabase import Client

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
      return response.data[0]

  except Exception as e:
    logger.error(f"Exception inserting angles: {e}")
    return {}

async def select(
  supabase: Client,
  logger,
  user_id: str,
  submission_ids
):
  try:

    response = (
      supabase.table("angles")
      .select("*")
      .eq("user_id", user_id)
      .in_("submission_id", submission_ids)
      .execute()
    )

    if response.data:
      return response.data[0]
    else:
      return None

  except Exception as e:
    logger.error(f"Failed to fetch angles based on token: {str(e)}")
    return None
