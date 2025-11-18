import streamlit as st
from partials.auth import (
  render_login,
  render_sign_up,
  render_forgot_password,
  render_onboarding
)
from renders.settings import render_settings
from renders.dashboard import render_dashboard
from renders.home import render_home

def run_page_flow():
  test_page = st.session_state["test_page"]

  if test_page == "login":
    render_login()

  elif test_page  == "sign_up":
    render_sign_up()

  elif test_page == "forgot":
    render_forgot_password()

  elif test_page == "onboarding":
    render_onboarding()

  elif test_page == "settings":
    render_settings()

  elif test_page == "dashboard":
    render_dashboard()

  elif test_page == "home":
    render_home()

  else:
    st.error(f"Unknown test_page: {test_page!r}")
