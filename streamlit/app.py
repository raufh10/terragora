import streamlit as st
from modules import SessionStateBuilder, PageSetter, run_page_flow
from streamlit_cookies_controller import CookieController
from modules.api import cookies_select  # 👈 import the cookies API wrapper

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

# Sync raw cookies into session_state["cookie"] for later usage
st.session_state["cookie"] = cookies

# --- Try to restore auth/session via cookies_select ---
token = st.session_state.get("cookie", {}).get("ajs_anonymous_id")
st.write("🔍 ajs_anonymous_id token from session_state['cookie']:", token)

if token:
  st.write("➡️ Calling cookies_select() with token...")
  try:
    cookie_resp = cookies_select(logger, token)
    st.write("📬 cookies_select() response:", cookie_resp)

    if cookie_resp.get("ok") and cookie_resp.get("data"):
      data = cookie_resp["data"]  # expected keys: user_id, user_email, access_token, refresh_token, token_expires_at
      st.write("✅ Cookie data payload:", data)

      st.session_state["user_id"] = data.get("user_id")
      st.session_state["user_email"] = data.get("user_email")
      st.session_state["auth_token"] = data.get("access_token")
      st.session_state["refresh_token"] = data.get("refresh_token")
      st.session_state["session_expires_at"] = data.get("token_expires_at")

      # mark as logged in if we have a user_id & token
      is_login = bool(st.session_state.get("user_id") and st.session_state.get("auth_token"))
      st.session_state["is_login"] = is_login

      st.write("👤 Restored user_id:", st.session_state.get("user_id"))
      st.write("📧 Restored user_email:", st.session_state.get("user_email"))
      st.write("🔑 Restored auth_token exists:", bool(st.session_state.get("auth_token")))
      st.write("🔄 Restored refresh_token exists:", bool(st.session_state.get("refresh_token")))
      st.write("⏳ Restored session_expires_at:", st.session_state.get("session_expires_at"))
      st.write("🔓 Restored is_login:", st.session_state.get("is_login"))
    else:
      st.write("⚠️ cookies_select returned not ok or no data; skipping restore.")
  except Exception as e:
    if logger:
      logger.exception(f"[COOKIES] Error calling cookies_select: {e}")
    st.write(f"❌ cookies_select failed: {e}")
else:
  st.write("⚠️ No ajs_anonymous_id token found in cookies; skipping cookies_select.")

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
