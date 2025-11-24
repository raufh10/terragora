import streamlit as st
from modules import SessionStateBuilder, PageSetter, run_page_flow
from streamlit_cookies_controller import CookieController
from modules.api import cookies_select, select_agenda_by_user_id

st.title("🧪 Partial Renderer Test")

st.write(st.query_params.to_dict())

# --- Session initialization ---
if "initiated" not in st.session_state:
  builder = SessionStateBuilder()
  builder.build()
else:
  pass

# --- Cookies load ---
cookie_ctrl = CookieController()
cookies = cookie_ctrl.getAll() or {}
st.session_state["cookie"] = cookies

# --- Try restore from cookies_select ---
token = st.session_state.get("cookie", {}).get("ajs_anonymous_id")

if token:
  try:
    cookie_resp = cookies_select(token)

    if cookie_resp.get("ok") and cookie_resp.get("data"):
      data = cookie_resp["data"]["data"]

      st.session_state["user_id"] = data.get("user_id")
      st.session_state["user_email"] = data.get("user_email")
      st.session_state["auth_token"] = data.get("access_token")
      st.session_state["refresh_token"] = data.get("refresh_token")
      st.session_state["session_expires_at"] = data.get("token_expires_at")

      st.session_state["is_login"] = bool(
        st.session_state.get("user_id") and st.session_state.get("auth_token")
      )

      # -------- Agenda restore added here --------
      user_id = st.session_state.get("user_id")
      if user_id:
        agenda_result = select_agenda_by_user_id(user_id)

        if agenda_result.get("ok") and agenda_result.get("data"):
          row = agenda_result["data"]

          st.session_state["agenda_id"] = row.get("id")
          st.session_state["user_name"] = row.get("user_name", "")
          st.session_state["agenda_name"] = row.get("name", "")
          st.session_state["agenda_subreddit"] = row.get("subreddit", "")
          st.session_state["agenda_type"] = row.get("type")
          st.session_state["agenda_location"] = row.get("location")

  except Exception as e:
    st.session_state["logger"].exception(f"[COOKIES] cookies_select error: {e}")

# --- Navigation ---
pages = PageSetter.get_pages()
pg = st.navigation(pages)
pg.run()

# Unified flow
run_page_flow()
