import streamlit as st

class PageSetter:

  @staticmethod
  def set_home():
    st.session_state["test_page"] = "home"

  @staticmethod
  def set_login():
    st.session_state["test_page"] = "auth"
    st.session_state["auth_panel"] = "login"

  @staticmethod
  def set_sign_up():
    st.session_state["test_page"] = "auth"
    st.session_state["auth_panel"] = "sign_up"

  @staticmethod
  def set_forgot():
    st.session_state["test_page"] = "auth"
    st.session_state["auth_panel"] = "forgot"

  @staticmethod
  def set_settings():
    st.session_state["test_page"] = "settings"

  @staticmethod
  def set_dashboard():
    st.session_state["test_page"] = "dashboard"

  @staticmethod
  def set_onboarding():
    st.session_state["test_page"] = "onboarding"

  # ---------- Pages dict for st.navigation ----------

  @classmethod
  def get_pages(cls) -> dict:

    is_login = st.session_state.get("is_login", False)

    pages = []

    if not is_login:
      pages.append(st.Page(cls.set_home, title="Home"))
      pages.append(st.Page(cls.set_login, title="Log in"))
      pages.append(st.Page(cls.set_sign_up, title="Sign up"))
    else:
      pages.append(st.Page(cls.set_dashboard, title="Dashboard"))
      pages.append(st.Page(cls.set_settings, title="Settings"))

    return pages
