from services.utils import FileLogger
from services.config import settings

def start_logger():

  file_logger = FileLogger(
    name=f"{settings.TITLE}-{settings.VERSION}",
    log_file=f"{settings.LOG_PATH}"
  )

  return file_logger.get_logger()
