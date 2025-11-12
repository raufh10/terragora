import streamlit as st
from pages.partials.auth import (
  render_login,
  render_sign_up,
  render_forgot_password,
)
from pages.partials.settings import render_settings
from pages.dashboard import render_dashboard  # ✅ imported here

# --- Toggle these for testing ---
test_page = "dashboard"   # "auth", "settings", or "dashboard"
auth_panel = "forgot"     # "login" | "sign_up" | "forgot"

# --- Page setup ---
st.set_page_config(
  page_title="Partial Test",
  page_icon="🧪",
  layout="centered",
)

st.title("🧪 Partial Renderer Test")

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
  render_dashboard()  # ✅ runs the dashboard feed renderer

else:
  st.error(f"Unknown test_page: {test_page!r}")
