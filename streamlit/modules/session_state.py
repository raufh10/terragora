import streamlit as st
from modules.api import get_supabase_client

class SessionStateBuilder:
  def __init__(self, logger):
    self._defaults = {
      "test_page": "auth",     # "auth" | "settings" | "dashboard" | "home"
      "auth_panel": "sign_up",   # only used when test_page == "auth"
      "is_first": True,       # NEW
      "db_client": get_supabase_client()
    }
    self.logger = logger

  def build(self):
    try:
      self.logger.info("🔧 Initializing session state for test runner")

      for key, value in self._defaults.items():
        if key not in st.session_state:
          st.session_state[key] = value
          self.logger.debug(
            f"Session key '{key}' initialized with default value: {value}"
          )
        else:
          self.logger.debug(
            f"Session key '{key}' already exists → {st.session_state[key]}"
          )

      self.logger.info("✅ Session state initialized")
      return st.session_state

    except Exception as e:
      self.logger.exception(f"💥 Error while building session state: {e}")
      return st.session_state
