from supabase import Client

async def insert(
  supabase: Client,
  logger,
  data: dict
):

  try:
    response = (
      supabase
      .table("cookies")
      .upsert(
        data,
        on_conflict="token"
      )
      .execute()
    )

    if response.data:
      return response.data[0]

  except Exception as e:
    logger.error(f"Exception upserting cookies: {e}")
    return {}

async def select(
  supabase: Client,
  logger,
  token: str
):
  try:

    response = (
      supabase.table("cookies")
      .select("*")
      .eq("token", token)
      .execute()
    )

    if response.data:
      return response.data[0]
    else:
      return None

  except Exception as e:
    logger.error(f"Failed to fetch cookies based on token: {str(e)}")
    return None

async def delete(
  supabase: Client,
  logger,
  token: str
):
  try:

    response = (
      supabase.table("cookies")
      .delete()
      .eq("token", token)
      .execute()
    )

    if response.data:
      return response.data[0]
    else:
      return None

  except Exception as e:
    logger.error(f"Failed to delete cookies based on token: {str(e)}")
    return None
