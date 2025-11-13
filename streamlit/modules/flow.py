import streamlit as st
from partials.auth import (
  render_login,
  render_sign_up,
  render_forgot_password,
)
from partials.settings import render_settings
from pages.dashboard import render_dashboard
from pages.home import render_home


def run_page_flow(test_page: str, auth_panel: str = "login"):
  """
  Routes to the correct page renderer based on the test_page and auth_panel.
  Everything is in 2-space indent.
  """

  if test_page == "auth":
    if auth_panel == "login":
      render_login()
    elif auth_panel == "sign_up":
      render_sign_up()
    elif auth_panel == "forgot":
      render_forgot_password()
    else:
      st.error(f"Unknown auth_panel: {auth_panel!r}")

  elif test_page == "settings":
    render_settings()

  elif test_page == "dashboard":
    render_dashboard()

  elif test_page == "home":
    render_home()

  else:
    st.error(f"Unknown test_page: {test_page!r}")
