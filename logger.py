from services.utils import FileLogger
from services.config import settings

def start_logger():

  file_logger = FileLogger(
    name=f"{settings.TITLE}-{settings.VERSION}",
    log_file=f"{settings.API_LOG_PATH}"
  )

  return file_logger.get_logger()
