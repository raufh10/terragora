import streamlit as st

from renders.settings import render_settings
from renders.dashboard import render_dashboard
from renders.home import render_home
from renders.login import render_login_page
from renders.sign_up import render_sign_up_page
from renders.forgot import render_forgot_page
from renders.onboarding import render_onboarding_page

def run_page_flow():
  test_page = st.session_state["test_page"]

  if test_page == "login":
    render_login_page()

  elif test_page  == "sign_up":
    render_sign_up_page()

  elif test_page == "forgot":
    render_forgot_page()

  elif test_page == "onboarding":
    render_onboarding_page()

  elif test_page == "settings":
    render_settings()

  elif test_page == "dashboard":
    render_dashboard()

  elif test_page == "home":
    render_home()

  else:
    st.error(f"Unknown test_page: {test_page!r}")
