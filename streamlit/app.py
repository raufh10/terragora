import streamlit as st
from modules import SessionStateBuilder, run_page_flow
from pages.logout import render_logout

from logger import start_logger
logger = start_logger()

def render_test():
  st.session_state["test_page"] = "settings"

# Sidebar test pages
pages = {
  "Your account": [
    st.Page(render_logout, title="Log Out"),
    st.Page(render_test, title="Test"),
  ]
}

pg = st.navigation(pages)
pg.run()

st.title("🧪 Partial Renderer Test")

# --- Session initialization logic ---
if "is_first" not in st.session_state:
  # First run → build session state
  builder = SessionStateBuilder(logger)
  builder.build()
else:
  logger.info("➡️ Session state already exists. Skipping builder.")

# --- Run unified flow ---
run_page_flow()
