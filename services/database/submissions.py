from supabase import Client
from services.database.agendas import select_subreddit

def has_accepted_subcategory(data, accepted):
  return any(item.get("subcategory") in accepted for item in data)

async def select(
  supabase: Client,
  logger,
  agenda_id: int,
  page: int = 1,
  per_page: int = 10,
  sort: str = "desc",
):
  try:
    subreddit, category = await select_subreddit(supabase, logger, agenda_id)
    if not subreddit:
      logger.warning(f"No subreddit found for agenda_id={agenda_id}")
      return []

    try:
      page = int(page)
    except Exception:
      page = 1
    try:
      per_page = int(per_page)
    except Exception:
      per_page = 10

    if page < 1:
      page = 1
    if per_page < 1:
      per_page = 10

    sort = (sort or "desc").lower()
    desc_flag = sort != "asc"

    start = (page - 1) * per_page
    end = start + per_page - 1

    response = (
      supabase
      .table("submissions")
      .select(
        "id, "
        "subreddit, "
        "category_data, "
        "data->title, "
        "data->link_flair_text, "
        "data->num_comments, "
        "data->created_utc, "
        "data->is_self, "
        "data->selftext, "
        "data->url"
      )
      .eq("subreddit", subreddit)
      .order("data->created_utc", desc=desc_flag)
      .range(start, end)
      .execute()
    )

    if response.data:
      return [item for item in response.data if has_accepted_subcategory(item.get("category_data", []), category)]
    else:
      return []

  except Exception as e:
    logger.error(f"Failed to fetch Submissions based on agenda id: {str(e)}")
    return None
