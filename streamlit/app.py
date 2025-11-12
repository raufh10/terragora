import streamlit as st
from pages.partials.auth import render_auth
from pages.partials.settings import render_settings

# --- Temporary test variable ---
# Change this manually to test: "auth" or "settings"
test_page = "auth"   # or "settings"

# --- Page setup ---
st.set_page_config(
  page_title="Test Page",
  page_icon="🧩",
  layout="centered",
)

st.title("🧪 Partial Renderer Test")

# --- Conditional rendering ---
if test_page == "auth":
  st.info("Rendering AUTH partial (login/signup/forgot).")
  render_auth()

elif test_page == "settings":
  st.info("Rendering SETTINGS partial.")
  render_settings()

else:
  st.warning(f"Unknown test_page: {test_page!r}")
