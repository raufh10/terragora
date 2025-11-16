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

has_session = cookies.get("has_session")
user_id = cookies.get("user_id")
user_email = cookies.get("user_email")

st.write("🔍 has_session =", has_session, "| type:", type(has_session))
st.write("🔍 user_id (cookie) =", user_id)
st.write("🔍 user_email (cookie) =", user_email)

# ✅ Looser condition: any truthy has_session + user_id present
if has_session and user_id:
  st.write("🍪✔ Valid session cookies detected. Rebuilding session_state from cookies...")

  st.session_state["user_id"] = user_id
  st.session_state["user_email"] = user_email
  st.session_state["is_login"] = True

  st.write("✅ session_state.user_id set:", st.session_state["user_id"])
  st.write("✅ session_state.user_email set:", st.session_state["user_email"])
  st.write("✅ session_state.is_login set to True")

else:
  st.write("ℹ️ No valid restoration cookies: has_session falsy or missing user_id.")

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
