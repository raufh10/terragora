import os
import json
import httpx
import logging

from typing import Optional
from urllib.parse import quote_plus
from services.config import settings, credentials

def send_telegram_notification(message: str):
  bot_token = quote_plus(credentials.telegram_bot_token.get_secret_value())
  user_id = quote_plus(credentials.telegram_user_id.get_secret_value())

  url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
  payload = {
    "chat_id": user_id,
    "text": message
  }

  with httpx.Client() as client:
    response = client.post(url, json=payload)

class JSONFormatter(logging.Formatter):
  def format(self, record):
    log_record = {
      'time': self.formatTime(record),
      'level': record.levelname,
      'logger': record.name,
      'filename': record.filename,
      'line': record.lineno,
      'function': record.funcName,
      'message': record.getMessage()
    }
    return json.dumps(log_record)

class TelegramHandler(logging.Handler):
  def emit(self, record):
    try:
      if record.levelno >= settings.TELEGRAM_BASE:
        log_entry = self.format(record)
        send_telegram_notification(log_entry)
    except Exception:
      self.handleError(record)

class FileLogger:
  def __init__(
    self,
    name: str,
    log_file: Optional[str] = None,
    level: int = settings.LOGGING_BASE,
    use_json: bool = True,
    log_format: Optional[str] = None
  ):
    log_format = log_format or '%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'

    self.logger = logging.getLogger(name)
    self.logger.setLevel(level)
    self.logger.propagate = False

    if not self.logger.handlers:
      if use_json:
        formatter = JSONFormatter()
      else:
        formatter = logging.Formatter(log_format)

      is_production = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV") == "production"

      if is_production:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)
      else:
        if not log_file:
          raise ValueError("log_file must be specified in development environment")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

      telegram_handler = TelegramHandler()
      telegram_handler.setLevel(logging.WARNING)
      telegram_handler.setFormatter(logging.Formatter(log_format))
      self.logger.addHandler(telegram_handler)

  def get_logger(self) -> logging.Logger:
    return self.logger
