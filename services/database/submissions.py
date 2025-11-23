from typing import Optional
from supabase import Client
from services.database.agendas import select_subreddit

def has_accepted_subcategory(data, accepted):
  if data is None:
    return False
  else:
    return any(item.get("subcategory") in accepted for item in data)

async def select(
  supabase: Client,
  logger,
  agenda_id: int,
  page: int = 1,
  per_page: int = 10,
  sort: str = "default",
  custom_category: Optional[str] = None,
  keyword: Optional[str] = None,
):
  try:
    subreddit, category = await select_subreddit(supabase, logger, agenda_id)
    if not subreddit:
      logger.warning(f"No subreddit found for agenda_id={agenda_id}")
      return []

    if custom_category:
      logger.info(f"🔧 Overriding category with custom_category='{custom_category}'")
      category = custom_category

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

    sort_normalized = (sort or "default").lower()
    sort_field_map = {
      "default": "data->created_utc",
      "num_comments": "data->num_comments",
      "scores": "data->score",
    }
    sort_field = sort_field_map.get(sort_normalized, "data->created_utc")
    desc_flag = True

    start = (page - 1) * per_page
    end = start + per_page - 1

    query = (
      supabase
      .table("submissions")
      .select(
        "id, "
        "subreddit, "
        "category_data, "
        "data->title, "
        "data->link_flair_text, "
        "data->num_comments, "
        "data->score, "
        "data->created_utc, "
        "data->is_self, "
        "data->selftext, "
        "data->url"
      )
      .eq("subreddit", subreddit)
      .not_.is_("category_data", "null")
    )

    if keyword:
      kw = str(keyword).strip()
      if kw:
        pattern = f"%{kw}%"
        query = query.like("data->title", pattern)

    response = (
      query
      .order(sort_field, desc=desc_flag)
      .range(start, end)
      .execute()
    )

    if not response.data:
      return []

    filtered = [
      item for item in response.data
      if has_accepted_subcategory(item.get("category_data", []), category)
    ]

    return filtered

  except Exception as e:
    logger.error(f"Failed to fetch Submissions based on agenda id: {str(e)}")
    return None

async def simple_select(
  supabase: Client,
  logger,
  submission_id: int
):
  try:

    response = (
      supabase.table("submissions")
      .select(
        "subreddit, "
        "data->title, "
        "data->link_flair_text, "
        "data->selftext"
      )
      .eq("id", submission_id)
      .execute()
    )

    if response.data:
      return response.data[0]
    else:
      return None

  except Exception as e:
    logger.error(f"Failed to fetch submissions based on submission_id: {str(e)}")
    return None
