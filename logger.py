from services.utils import FileLogger

TITLE: str = "LeadditsScheduler"
VERSION: str = "1.0.0"
LOG_PATH: str = "./logs/app.log"

def start_logger():

  file_logger = FileLogger(
    name=f"{TITLE}-{VERSION}",
    log_file=f"{LOG_PATH}"
  )

  return file_logger.get_logger()
