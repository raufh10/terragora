import streamlit as st
from modules import SessionStateBuilder, PageSetter, run_page_flow
from streamlit_cookies_controller import CookieController

from logger import start_logger
logger = start_logger()

st.title("🧪 Partial Renderer Test")

st.write("🚀 App start — beginning initialization")

# --- Session initialization logic ---
if "initiated" not in st.session_state:
  st.write("🔧 Running SessionStateBuilder() for the first time...")
  builder = SessionStateBuilder(logger)
  builder.build()
  st.write("✅ SessionStateBuilder finished.")
else:
  st.write("ℹ️ Session state already exists — skipping builder.")

# --- Try to restore session from cookies (always check) ---
st.write("📥 Loading cookies using CookieController...")
cookie_ctrl = CookieController()
cookies = cookie_ctrl.getAll() or {}

st.write("🍪 Cookies found:", cookies)

# --- Navigation ---
st.write("📦 Current session_state snapshot:")
st.write(st.session_state)

st.write("🧭 Loading pages from PageSetter...")
pages = PageSetter.get_pages()
pg = st.navigation(pages)
st.write("🧭 Starting navigation...")
pg.run()

# --- Run unified flow ---
st.write("🔁 Running unified page flow...")
run_page_flow()

st.write("🏁 End of script. Session login status =", st.session_state.get("is_login"))
