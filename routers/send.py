from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, constr

from services.config.settings import settings
from services.utils.file_logger import send_telegram_notification as _tg_send

from logger import start_logger
logger = start_logger()
router = APIRouter()

class TelegramNotifyPayload(BaseModel):
  message: constr(
    strip_whitespace=True,
    min_length=settings.TELEGRAM_MIN_LENGHT,
    max_length=settings.TELEGRAM_MAX_LENGHT
  ) = Field(...)

@router.post("/telegram")
async def notify_telegram(payload: TelegramNotifyPayload):
  msg = payload.message if isinstance(payload.message, str) else ""
  length = len(msg) if msg else 0
  logger.info(f"📨 Telegram notify request | length={length}")

  if not msg:
    logger.warning("⚠️ Empty or invalid 'message' payload")
    raise HTTPException(status_code=400, detail="Message cannot be empty")

  try:
    preview = (msg[:120] + "…") if len(msg) > 120 else msg
    logger.debug(f"✉️ Message preview: {preview!r}")

    try:
      _tg_send(msg)
    except HTTPException as http_err:
      logger.error(f"🚫 Telegram send HTTP error | status={http_err.status_code} detail={http_err.detail}")
      raise
    except Exception as send_err:
      logger.error(f"💥 Error calling send_telegram_notification | error={str(send_err)}")
      raise

    logger.info("✅ Telegram notification sent")
    return {
      "ok": True,
      "message": "Notification sent"
    }

  except HTTPException:
    raise
  
  except Exception:
    logger.exception("💥 Unhandled error during telegram notify")
    raise HTTPException(status_code=500, detail="Internal server error")