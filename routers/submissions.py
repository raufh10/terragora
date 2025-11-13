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
  supabase: Client = Depends(db.get_supabase_client),
):
  logger.info(f"📥 /submissions/{agenda_id}/feed")
  try:
    if not agenda_id or agenda_id <= 0:
      raise HTTPException(status_code=400, detail="agenda_id must be a positive integer")

    rows = await submissions.select(supabase, logger, agenda_id)

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
      "count": count,
      "data": rows,
    }

  except HTTPException:
    raise
  except Exception:
    logger.exception(f"💥 Unhandled error in /submissions/{agenda_id}/feed")
    raise HTTPException(status_code=500, detail="Internal server error")
