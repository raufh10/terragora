import os
import json
import logging
from typing import Optional
from modules.api import send_telegram_notification

class JSONFormatter(logging.Formatter):
  """Minimal JSON log formatter: time, level, logger, message, and location."""
  def format(self, record: logging.LogRecord) -> str:
    log_record = {
      "time": self.formatTime(record),
      "level": record.levelname,
      "logger": record.name,
      "message": record.getMessage(),
      "where": f"{record.filename}:{record.lineno}",
    }
    return json.dumps(log_record)

class TelegramHandler(logging.Handler):
  """
  Sends WARNING+ logs to Telegram, with a concise human-readable format.
  """
  def __init__(self, level: int = logging.ERROR):
    super().__init__(level)

  def emit(self, record: logging.LogRecord) -> None:
    try:
      if record.levelno >= self.level:
        # Very concise message for Telegram
        msg = f"[{record.levelname}] {record.getMessage()} ({record.filename}:{record.lineno})"
        send_telegram_notification(msg)
    except Exception:
      self.handleError(record)

class FileLogger:
  def __init__(
    self,
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    use_json: bool = True,
  ):
    """
    - In production (RAILWAY_ENVIRONMENT or ENV=production):
        * Always log to stdout (StreamHandler).
        * JSON format if use_json=True, otherwise plain text.
    - In local/dev:
        * Always log to stdout (StreamHandler) with concise text.
        * Optionally log to file if log_file is provided.
    - Telegram:
        * Sends WARNING+ with a short human-readable message.
    """
    self.logger = logging.getLogger(name)
    self.logger.setLevel(level)
    self.logger.propagate = False

    if self.logger.handlers:
      # Already configured, don't attach duplicate handlers
      return

    is_production = bool(
      os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV") == "production"
    )

    # -------- Console / stream handler (always enabled) --------
    if is_production and use_json:
      console_formatter: logging.Formatter = JSONFormatter()
    else:
      # Concise readable format for local/dev and non-JSON prod
      console_formatter = logging.Formatter(
        "[%(levelname)s] %(asctime)s - %(message)s"
      )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(console_formatter)
    self.logger.addHandler(stream_handler)

    # -------- Optional file handler (mainly for local/dev) --------
    if log_file:
      try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
      except Exception:
        # If dirname is empty or mkdir fails, just skip file logging
        pass
      else:
        file_formatter: logging.Formatter = (
          JSONFormatter()
          if use_json
          else logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s "
            "(%(filename)s:%(lineno)d)"
          )
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    # -------- Telegram handler (WARNING and above) --------
    telegram_handler = TelegramHandler(level=logging.WARNING)
    # Simple human-friendly format; TelegramHandler uses only record.getMessage(),
    # but we keep this in case we reuse formatter elsewhere.
    telegram_handler.setFormatter(logging.Formatter("%(message)s"))
    self.logger.addHandler(telegram_handler)

  def get_logger(self) -> logging.Logger:
    return self.logger
