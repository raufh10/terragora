import streamlit as st
from modules import SessionStateBuilder, PageSetter, run_page_flow
from modules.api import set_session_from_tokens

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
access_token = cookies.get("access_token")
refresh_token = cookies.get("refresh_token")

st.write("🔍 has_session =", has_session)
st.write("🔍 access_token exists =", bool(access_token))
st.write("🔍 refresh_token exists =", bool(refresh_token))

# Attempt restore
if has_session == "1" and access_token and refresh_token:
  st.write("🍪✔ Valid session cookies detected. Attempting auto-restore...")
  logger.info("🍪 Attempting session restore from cookies.")

  # Set into session_state
  st.write("📦 Storing tokens into session_state...")
  st.session_state["auth_token"] = access_token
  st.session_state["refresh_token"] = refresh_token

  user_id = cookies.get("user_id")
  user_email = cookies.get("user_email")
  session_expires_at = cookies.get("session_expires_at")

  st.write("📦 user_id (cookie) =", user_id)
  st.write("📦 user_email (cookie) =", user_email)
  st.write("📦 session_expires_at (cookie) =", session_expires_at)

  if user_id:
    st.session_state["user_id"] = user_id
    st.write("✅ session_state.user_id set.")
  if user_email:
    st.session_state["user_email"] = user_email
    st.write("✅ session_state.user_email set.")

  # Parse expires_at
  if session_expires_at is not None:
    st.write("⏳ Parsing session_expires_at...")
    try:
      st.session_state["session_expires_at"] = float(session_expires_at)
      st.write("⏳✔ Parsed expires_at successfully:", st.session_state["session_expires_at"])
    except Exception as e:
      st.write("⚠️ Failed to parse session_expires_at:", e)

  # Get db_client
  supabase = st.session_state.get("db_client")
  st.write("🔌 Supabase client loaded =", bool(supabase))

  if supabase:
    st.write("➡️ Calling set_session_from_tokens()...")
    resp = set_session_from_tokens(
      supabase=supabase,
      logger=logger,
      access_token=access_token,
      refresh_token=refresh_token,
    )

    st.write("📬 Response from set_session_from_tokens:", resp)

    if resp.get("ok"):
      st.write("🎉 SUCCESS: Session restored from cookies!")
      st.session_state["is_login"] = True
    else:
      st.write("❌ set_session_from_tokens returned failure.")
      st.write("🛑 User will remain logged out.")
  else:
    st.write("⚠️ No db_client — cannot restore session.")
else:
  st.write("ℹ️ No valid restoration cookies: has_session!=1 or missing token(s).")

# --- Navigation ---
st.write("🧭 Loading pages from PageSetter...")
pages = PageSetter.get_pages()
pg = st.navigation(pages)
st.write("🧭 Starting navigation...")
pg.run()

# --- Run unified flow ---
st.write("🔁 Running unified page flow...")
run_page_flow()

st.write("🏁 End of script. Session login status =", st.session_state.get("is_login"))
