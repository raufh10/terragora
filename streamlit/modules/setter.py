import streamlit as st
from modules.api import cookies_delete

class PageSetter:

  @staticmethod
  def set_home():
    st.session_state["test_page"] = "home"

  @staticmethod
  def set_login():
    st.session_state["test_page"] = "login"

  @staticmethod
  def set_sign_up():
    st.session_state["test_page"] = "sign_up"

  @staticmethod
  def set_onboarding():
    st.session_state["test_page"] = "onboarding"

  @staticmethod
  def set_forgot():
    st.session_state["test_page"] = "forgot"

  @staticmethod
  def set_settings():
    st.session_state["test_page"] = "settings"

  @staticmethod
  def set_dashboard():
    st.session_state["test_page"] = "dashboard"

  @staticmethod
  def set_logout():
    logger = st.session_state.get("logger")
    token = st.session_state.get("cookie", {}).get("ajs_anonymous_id", "")
    cookies_delete(logger, token)

  # ---------- Pages dict for st.navigation ----------

  @classmethod
  def get_pages(cls) -> dict:

    is_login = st.session_state.get("is_login", False)
    is_onboarding = st.session_state.get("is_onboarding", False)

    pages = []

    if is_onboarding:
      st.write("is_onboarding")
      pages.append(st.Page(cls.set_onboarding, title="Onboarding"))
      return pages

    if not is_login:
      st.write("is_not_login")
      pages.append(st.Page(cls.set_home, title="Home"))
      pages.append(st.Page(cls.set_login, title="Log in"))
      pages.append(st.Page(cls.set_sign_up, title="Sign up"))
    else:
      st.write("is_login")
      pages.append(st.Page(cls.set_dashboard, title="Dashboard"))
      pages.append(st.Page(cls.set_settings, title="Settings"))
      pages.append(st.Page(cls.set_logout, title="Log Out"))

    return pages
