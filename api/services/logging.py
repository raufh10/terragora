import logging
import sys
import httpx
from services.config import configs

BOT_TOKEN = configs.notification_telegram_bot_token.get_secret_value()
USER_ID = configs.notification_telegram_user_id.get_secret_value()
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

class TelegramHandler(logging.Handler):
  def emit(self, record):
    should_notify = record.levelno >= logging.WARNING or getattr(record, "notify", False)
    
    if not should_notify:
      return

    log_entry = self.format(record)
    try:
      prefix = "🔔 *Incoming Message*" if getattr(record, "notify", False) else "⚠️ *Bot Alert*"
      
      payload = {
        "chat_id": USER_ID,
        "text": f"{prefix}\n`{log_entry}`",
        "parse_mode": "Markdown"
      }

      with httpx.Client(timeout=5.0) as client:
        client.post(API_URL, json=payload)

    except Exception as e:
      sys.stderr.write(f"Telegram Logging Failed: {e}\n")

def setup_logger(name: str) -> logging.Logger:
  log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  date_format = "%Y-%m-%d %H:%M:%S"

  console_handler = logging.StreamHandler(sys.stdout)
  console_handler.setFormatter(logging.Formatter(log_format, date_format))

  tg_handler = TelegramHandler()
  tg_handler.setLevel(logging.INFO) 
  tg_handler.setFormatter(logging.Formatter(log_format, date_format))

  root_logger = logging.getLogger()
  root_logger.setLevel(logging.INFO)
  
  if not root_logger.handlers:
    root_logger.addHandler(console_handler)
    root_logger.addHandler(tg_handler)

  return logging.getLogger(name)

logger = setup_logger("leaddits_app")
