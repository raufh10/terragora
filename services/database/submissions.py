from supabase import Client
from services.database.agendas import select_subreddit

async def select(
  supabase: Client,
  logger,
  agenda_id: int
):
  try:
    subreddit = await select_subreddit(supabase, logger, agenda_id)

    response = (
      supabase.table("submissions")
      .select("id, data, category")
      .eq("subreddit", subreddit)
      .execute()
    )

    if response.data:
      return response.data
    else:
      return []

  except Exception as e:
    logger.error(f"Failed to fetch Submissions based on agenda id: {str(e)}")
    return None
