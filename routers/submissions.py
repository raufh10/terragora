from typing import Optional, Dict, Any
from fastapi import APIRouter, Body, HTTPException, Depends
from supabase import Client

from services.database import db, submissions, angles, agendas
from logger import start_logger

logger = start_logger()
router = APIRouter()

@router.post("/submissions/{agenda_id}/feed")
async def submissions_feed(
  agenda_id: int,
  payload: Optional[Dict[str, Any]] = Body(None),
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info(f"📥 /submissions/{agenda_id}/feed")
  try:
    if not agenda_id or agenda_id <= 0:
      raise HTTPException(status_code=400, detail="agenda_id must be a positive integer")

    payload = payload or {}
    page = payload.get("page", 1)
    per_page = payload.get("per_page", 10)
    sort = payload.get("sort", "default")
    keyword = payload.get("keyword")
    custom_category = payload.get("category")

    try:
      page_int = int(page)
    except Exception:
      page_int = 1

    try:
      per_page_int = int(per_page)
    except Exception:
      per_page_int = 10

    sort_str = str(sort or "default").lower()
    allowed_sorts = {"default", "num_comments", "scores"}
    if sort_str not in allowed_sorts:
      logger.warning(f"⚠️ Invalid sort='{sort_str}', falling back to 'default'")
      sort_str = "default"

    rows = await submissions.select(
      supabase,
      logger,
      agenda_id,
      page=page_int,
      per_page=per_page_int,
      sort=sort_str,
      custom_category=custom_category,
      keyword=keyword,
    )

    if rows is None:
      logger.error(f"⚠️ submissions.select returned None for agenda_id={agenda_id}")
      raise HTTPException(status_code=502, detail="Failed to load submissions")

    new_rows = []

    if rows:
      user_id = await agendas.select_user_id(supabase, logger, agenda_id)
      collected_submission_ids = [item["id"] for item in rows]
      angles_result = await angles.select(supabase, logger, user_id, collected_submission_ids) or []

      angles_by_sub_id = {
        item.get("submission_id"): item.get("data")
        for item in angles_result
        if item.get("submission_id") is not None
      }

      for item in rows:
        row = dict(item)
        sub_id = row.get("id")
        row["angles_data"] = angles_by_sub_id.get(sub_id)
        new_rows.append(row)

    count = len(new_rows)

    return {
      "ok": True,
      "agenda_id": agenda_id,
      "page": page_int,
      "per_page": per_page_int,
      "sort": sort_str,
      "keyword": keyword,
      "category": custom_category,
      "count": count,
      "data": new_rows,
    }

  except HTTPException:
    raise
  except Exception:
    logger.exception(f"💥 Unhandled error in /submissions/{agenda_id}/feed")
    raise HTTPException(status_code=500, detail="Internal server error")
