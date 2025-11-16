from typing import Optional, Dict, Any
from fastapi import APIRouter, Body, HTTPException, Depends
from supabase import Client

from services.database import db, submissions
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
    sort = payload.get("sort", "desc")

    try:
      page_int = int(page)
    except Exception:
      page_int = 1

    try:
      per_page_int = int(per_page)
    except Exception:
      per_page_int = 10

    sort_str = str(sort or "desc").lower()

    rows = await submissions.select(
      supabase,
      logger,
      agenda_id,
      page=page_int,
      per_page=per_page_int,
      sort=sort_str,
    )

    if rows is None:
      logger.error(f"⚠️ submissions.select returned None for agenda_id={agenda_id}")
      raise HTTPException(status_code=502, detail="Failed to load submissions")

    if isinstance(rows, list):
      count = len(rows)
    else:
      count = 1

    return {
      "ok": True,
      "agenda_id": agenda_id,
      "page": page_int,
      "per_page": per_page_int,
      "sort": sort_str,
      "count": count,
      "data": rows,
    }

  except HTTPException:
    raise
  except Exception:
    logger.exception(f"💥 Unhandled error in /submissions/{agenda_id}/feed")
    raise HTTPException(status_code=500, detail="Internal server error")
