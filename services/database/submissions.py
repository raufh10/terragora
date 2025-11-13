from supabase import Client

async def select(
  supabase: Client,
  logger,
  subreddit: str
):
  try:

    response = (
      supabase.table("submissions")
      .select("id, data, category, agendas(id, subreddit)")
      .execute()
    )

    if response.data:
      return [item for item in response.data if item["agendas"]["subreddit"] == subreddit]
    else:
      return []

  except Exception as e:
    logger.error(f"Failed to fetch Submissions based on subreddit id: {str(e)}")
    return None
