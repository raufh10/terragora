import streamlit as st

class SessionStateBuilder:
  def __init__(self, logger):
    self._defaults = {
      "token": "",
      "mode": "upload_resume",
      "resume": {},
      "user_profile": {},
      "confirmation": {},
    }
    self.logger = logger

  def build(self):
    try:
      self.logger.info("🔧 Initializing session state with defaults if missing")
      for key, value in self._defaults.items():
        if key not in st.session_state:
          st.session_state[key] = value
          self.logger.debug(f"Session key '{key}' initialized with default value")
        else:
          self.logger.debug(f"Session key '{key}' already exists, keeping current value")
      self.logger.info("✅ Session state initialization complete")
      return st.session_state
    except Exception as e:
      self.logger.exception(f"💥 Error while building session state: {e}")
      return st.session_state

class DashboardSessionStateBuilder:
  def __init__(self, logger):
    self._defaults = {
      "user_profile": {},
      "alert_data": [],
    }
    self.logger = logger

  def build(self):
    try:
      self.logger.info("🔧 Initializing session state with defaults if missing")
      for key, value in self._defaults.items():
        if key not in st.session_state:
          st.session_state[key] = value
          self.logger.debug(f"Session key '{key}' initialized with default value")
        else:
          self.logger.debug(f"Session key '{key}' already exists, keeping current value")
      self.logger.info("✅ Session state initialization complete")
      return st.session_state
    except Exception as e:
      self.logger.exception(f"💥 Error while building session state: {e}")
      return st.session_state