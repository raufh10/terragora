import streamlit as st
from modules import SessionStateBuilder, run_page_flow

# Temporary test variables
test_page = "home"       # "auth" | "settings" | "dashboard" | "home"
auth_panel = "login"     # only used when test_page == "auth"

st.set_page_config(
  page_title="Partial Test",
  page_icon="🧪",
  layout="centered",
)

st.title("🧪 Partial Renderer Test")

# Run the unified flow
run_page_flow(test_page, auth_panel)
