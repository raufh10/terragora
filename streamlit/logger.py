from modules.utils import FileLogger

def start_logger():

  file_logger = FileLogger(
    name="JoblitWeb-v1",
    log_file="./logs/streamlit.log"
  )

  return file_logger.get_logger()
