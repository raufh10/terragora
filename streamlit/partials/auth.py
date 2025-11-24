import time
import streamlit as st
from modules.api import (
  cookies_create,
  sign_in,
  sign_up,
  select_agenda_by_user_id,
  create_agenda,
  reset_password_for_email
)
from modules.setter import PageSetter
from modules.config import TYPE_OPTIONS, LOCATION_OPTIONS


# --------------------------
# LOGIN
# --------------------------
def render_login():
  st.header("🔐 Log in")

  supabase = st.session_state.get("db_client")
  if not supabase:
    st.error("Supabase client missing.")
    return

  with st.form("login_form"):
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    submitted = st.form_submit_button("Sign in")

    if submitted:
      logger = st.session_state.get("logger")
      result = sign_in(supabase, email, password)

      if result.get("ok"):
        auth_resp = result.get("data")
        if auth_resp is None:
          st.error("Login succeeded but no auth data.")
          return

        session_obj = getattr(auth_resp, "session", None)
        user_obj = getattr(auth_resp, "user", None)

        if session_obj is None:
          st.error("Login succeeded but missing session.")
          return

        # Store session info in session_state only (no tokens in cookies)
        st.session_state["auth_token"] = getattr(session_obj, "access_token", None)
        st.session_state["refresh_token"] = getattr(session_obj, "refresh_token", None)
        st.session_state["session_expires_at"] = getattr(session_obj, "expires_at", None)

        # Store user info
        if user_obj is not None:
          st.session_state["user_id"] = getattr(user_obj, "id", None)
          st.session_state["user_email"] = getattr(user_obj, "email", email)
        else:
          st.session_state["user_id"] = None
          st.session_state["user_email"] = email

        # ---- Fetch agenda/profile from backend ----
        user_id = st.session_state.get("user_id")

        if user_id:
          try:
            agenda_result = select_agenda_by_user_id(user_id)

            if agenda_result.get("ok") and agenda_result.get("data"):
              row = agenda_result["data"]

              st.session_state["agenda_id"] = row.get("id")
              st.session_state["user_name"] = row.get("user_name", "")
              st.session_state["agenda_name"] = row.get("name", "")
              st.session_state["agenda_subreddit"] = row.get("subreddit", "")
              st.session_state["agenda_type"] = row.get("type")
              st.session_state["agenda_location"] = row.get("location")

              logger.info(f"[SETTINGS] Loaded agenda for user_id={user_id}")

            else:
              logger.warning(f"[SETTINGS] select_agenda_by_user_id not ok: {agenda_result}")

          except Exception as e:
            logger.exception(f"[SETTINGS] Error calling select_agenda_by_user_id: {e}")
            st.warning("Could not load agenda from backend; using defaults.")

        else:
          logger.info("[SETTINGS] Missing user_id; using defaults")

        # --------------------------
        # Persist session in backend cookies table
        # --------------------------
        cookies_state = st.session_state.get("cookies") or {}
        token = None
        if isinstance(cookies_state, dict):
          token = cookies_state.get("ajs_anonymous_id")

        if token:
          cookie_data = {
            "user_id": st.session_state.get("user_id"),
            "user_email": st.session_state.get("user_email"),
            "access_token": st.session_state.get("auth_token"),
            "refresh_token": st.session_state.get("refresh_token"),
            "token_expires_at": st.session_state.get("session_expires_at"),
          }
          cookie_result = cookies_create(token, cookie_data)
          if not cookie_result.get("ok"):
            logger.warning(f"[COOKIES] cookies_create not ok: {cookie_result}")
        else:
          logger.warning("[COOKIES] Missing ajs_anonymous_id; skipping cookies_create")

        # Mark logged in and switch page
        st.session_state["is_login"] = True
        PageSetter.set_dashboard()
        st.rerun()

      else:
        st.error(result.get("error", "Login failed."))

  st.divider()

  st.caption("Forgot your password?")
  if st.button("🔁 Reset password"):
    render_forgot_password()

  st.caption("New here?")
  if st.button("📝 Create account"):
    st.session_state["auth_panel"] = "sign_up"


# --------------------------
# SIGN UP
# --------------------------
def render_sign_up():
  st.header("📝 Create account")

  supabase = st.session_state.get("db_client")
  if not supabase:
    st.error("Supabase client missing: session_state['db_client'] not set.")
    return

  with st.form("signup_form"):
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
    submitted = st.form_submit_button("Create account")

    if submitted:
      if password != confirm:
        st.error("Passwords do not match.")
        return

      logger = st.session_state.get("logger")
      result = sign_up(supabase, email, password)

      if result.get("ok"):
        auth_resp = result.get("data")
        if auth_resp is None:
          st.error("Sign up succeeded but no auth data.")
          return

        session_obj = getattr(auth_resp, "session", None)
        user_obj = getattr(auth_resp, "user", None)

        if session_obj is None:
          st.error("Sign up succeeded but missing session.")
          return

        # Store session info in session_state only (no tokens in cookies)
        st.session_state["auth_token"] = getattr(session_obj, "access_token", None)
        st.session_state["refresh_token"] = getattr(session_obj, "refresh_token", None)
        st.session_state["session_expires_at"] = getattr(session_obj, "expires_at", None)

        # Store user info
        if user_obj is not None:
          st.session_state["user_id"] = getattr(user_obj, "id", None)
          st.session_state["user_email"] = getattr(user_obj, "email", email)
        else:
          st.session_state["user_id"] = None
          st.session_state["user_email"] = email

        # Call cookies_create with ajs_anonymous_id
        cookies_dict = st.session_state.get("cookies") or {}
        token = cookies_dict.get("ajs_anonymous_id")

        if token:
          cookie_data = {
            "user_id": st.session_state.get("user_id"),
            "user_email": st.session_state.get("user_email"),
            "access_token": st.session_state.get("auth_token"),
            "refresh_token": st.session_state.get("refresh_token"),
            "token_expires_at": st.session_state.get("session_expires_at"),
          }

          cookie_result = cookies_create(token, cookie_data)
          if not cookie_result.get("ok"):
            logger.warning(f"[COOKIES] cookies_create not ok: {cookie_result}")
        else:
          logger.warning("[COOKIES] No ajs_anonymous_id in session_state['cookies']; skipping cookies_create")

        # Mark is_onboarding
        st.session_state["is_onboarding"] = True

        # Then go to onboarding
        PageSetter.set_onboarding()
        st.rerun()

      else:
        st.error(result.get("error", "Sign up failed."))

  if st.button("⬅ Back to login"):
    st.session_state["auth_panel"] = "login"


# --------------------------
# FORGOT PASSWORD
# --------------------------
@st.dialog("Forgot password")
def render_forgot_password():

  """
  st.header("🔁 Reset password")
  """

  supabase = st.session_state.get("db_client")
  logger = st.session_state.get("logger")

  if not supabase:
    st.error("Supabase client missing: session_state['db_client'] not set.")
    return

  st.write("Enter your email and we’ll send a reset link to your inbox.")
  with st.form("forgot_form"):
    email = st.text_input("Email", key="forgot_email")
    submitted = st.form_submit_button("Send reset link")

    if submitted:
      if not email:
        st.error("Please enter your email address.")
        return

      result = reset_password_for_email(
        supabase=supabase,
        email=email,
        redirect_to="https://website-production-1286.up.railway.app/?first_key="
      )

      if result.get("ok"):
        st.success(f"Reset link sent to **{email}**.")
      else:
        st.error(result.get("error", "Failed to send reset email."))

# --------------------------
# ONBOARDING
# --------------------------
def render_onboarding():
  st.header("🎉 Welcome! Let's set up your first agenda.")

  user_id = st.session_state.get("user_id")
  logger = st.session_state.get("logger")

  if not user_id:
    st.error("Missing user ID. Please log in again.")
    return

  # -------------------------
  # FORM
  # -------------------------
  with st.form("onboarding_form"):
    st.subheader("👤 Your Name")
    user_name = st.text_input("Your Name")

    st.subheader("🗓️ Agenda Setup")

    agenda_name = st.text_input("Agenda name")
    subreddit = st.text_input("Subreddit")

    st.write("📌 Select Type")
    type_choice = st.multiselect("Type", TYPE_OPTIONS)

    st.write("📌 Select Location")
    location_choice = st.selectbox("Location", LOCATION_OPTIONS)

    submitted = st.form_submit_button("Create agenda")

  # -------------------------
  # ON SUBMIT
  # -------------------------
  if submitted:
    if not user_name or not agenda_name or not subreddit:
      st.error("All fields are required.")
      return

    payload_data = {
      "type": type_choice,
      "location": location_choice,
    }

    result = create_agenda(
      subreddit=subreddit,
      user_id=user_id,
      name=agenda_name,
      user_name=user_name,
      data=payload_data,
    )

    if not result.get("ok"):
      st.error(result.get("error", "Failed to create agenda."))
      return

    # -------------------------
    # SAVE DATA TO SESSION STATE
    # -------------------------
    row = result.get("data") or {}

    st.session_state["agenda_id"] = row.get("id")
    st.session_state["agenda_name"] = row.get("name")
    st.session_state["agenda_subreddit"] = row.get("subreddit")
    st.session_state["agenda_type"] = row.get("data", {}).get("type")
    st.session_state["agenda_location"] = row.get("data", {}).get("location")
    st.session_state["user_name"] = row.get("user_name")

    st.session_state["is_login"] = True
    st.success("🎉 Agenda created! Redirecting to dashboard...")

    # Mark is_onboarding
    st.session_state["is_onboarding"] = False

    PageSetter.set_dashboard()
    st.rerun()
