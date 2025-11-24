import streamlit as st
from modules.api import get_supabase_client
from modules.utils import FileLogger

def start_logger():
  logger_builder = FileLogger(
    name="LeadditsWeb",
    log_file="./logs/streamlit.log",
    level="INFO",
    use_json=True
  )
  return logger_builder.get_logger()

class SessionStateBuilder:
  def __init__(self):
    self._defaults = {
      "test_page": "auth",
      "initiated": True,
      "db_client": get_supabase_client(),
      "is_login": False,
    }

  def build(self):
    try:
      logger = start_logger()
      st.session_state["logger"] = logger

      for key, value in self._defaults.items():
        if key not in st.session_state:
          st.session_state[key] = value
          logger.debug(f"Session key '{key}' initialized → {value}")
        else:
          logger.debug(f"Session key '{key}' already exists → {st.session_state[key]}")

      logger.info("Session state initialized")
      return st.session_state

    except Exception as e:
      if "logger" in st.session_state and st.session_state["logger"]:
        st.session_state["logger"].exception(f"Error while building session state: {e}")
      return st.session_state
