import time
import streamlit as st
from modules.api import sign_in, sign_up, reset_password_for_email, select_agenda_by_user_id, create_agenda
from modules.setter import PageSetter
from modules.config import TYPE_OPTIONS, LOCATION_OPTIONS

# --------------------------
# LOGIN
# --------------------------
def render_login():
  st.header("🔐 Log in")

  st.write("🧪 render_login() started")

  supabase = st.session_state.get("db_client")
  st.write("🔌 Supabase client exists:", bool(supabase))

  if not supabase:
    st.error("Supabase client missing.")
    return

  with st.form("login_form"):
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    submitted = st.form_submit_button("Sign in")

    if submitted:
      st.write("📨 Login form submitted")
      st.write("📧 Email entered:", email)

      logger = st.session_state.get("logger")
      st.write("📝 Logger exists:", bool(logger))

      st.write("➡️ Calling sign_in()...")
      result = sign_in(supabase, logger, email, password)
      st.write("📬 sign_in() result:", result)

      if result.get("ok"):
        st.write("✅ sign_in returned ok")

        auth_resp = result.get("data")
        st.write("📦 auth_resp present:", auth_resp is not None)

        if auth_resp is None:
          st.error("Login succeeded but no auth data.")
          return

        session_obj = getattr(auth_resp, "session", None)
        user_obj = getattr(auth_resp, "user", None)

        st.write("📦 session_obj present:", session_obj is not None)
        st.write("📦 user_obj present:", user_obj is not None)

        if session_obj is None:
          st.error("Login succeeded but missing session.")
          return

        # Store session info in session_state only (no tokens in cookies)
        st.session_state["auth_token"] = getattr(session_obj, "access_token", None)
        st.session_state["refresh_token"] = getattr(session_obj, "refresh_token", None)
        st.session_state["session_expires_at"] = getattr(session_obj, "expires_at", None)

        st.write("🔑 auth_token exists:", bool(st.session_state["auth_token"]))
        st.write("🔄 refresh_token exists:", bool(st.session_state["refresh_token"]))
        st.write("⏳ session_expires_at:", st.session_state["session_expires_at"])

        # Store user info
        if user_obj is not None:
          st.session_state["user_id"] = getattr(user_obj, "id", None)
          st.session_state["user_email"] = getattr(user_obj, "email", email)
        else:
          st.session_state["user_id"] = None
          st.session_state["user_email"] = email

        st.write("👤 user_id:", st.session_state["user_id"])
        st.write("👤 user_email:", st.session_state["user_email"])

        # ---- Fetch agenda/profile from backend ----
        user_id = st.session_state.get("user_id")
        st.write("🔍 Using user_id for agenda fetch:", user_id)

        if user_id:
          try:
            st.write("➡️ Calling select_agenda_by_user_id()...")
            agenda_result = select_agenda_by_user_id(logger, user_id)
            st.write("📬 select_agenda_by_user_id() raw result:", agenda_result)

            if agenda_result.get("ok") and agenda_result.get("data"):
              row = agenda_result["data"]
              st.write("✅ Agenda row loaded:", row)

              st.session_state["agenda_id"] = row.get("id")
              st.session_state["user_name"] = row.get("user_name", "")
              st.session_state["agenda_name"] = row.get("name", "")
              st.session_state["agenda_subreddit"] = row.get("subreddit", "")
              st.session_state["agenda_type"] = row.get("type")
              st.session_state["agenda_location"] = row.get("location")

              st.write("🧩 agenda_id:", st.session_state.get("agenda_id"))
              st.write("🧩 user_name:", st.session_state.get("user_name"))
              st.write("🧩 agenda_name:", st.session_state.get("agenda_name"))
              st.write("🧩 agenda_subreddit:", st.session_state.get("agenda_subreddit"))
              st.write("🧩 agenda_type:", st.session_state.get("agenda_type"))
              st.write("🧩 agenda_location:", st.session_state.get("agenda_location"))

              if logger:
                logger.info(f"[SETTINGS] Loaded agenda for user_id={user_id}")
            else:
              st.write("⚠️ select_agenda_by_user_id returned not ok or no data")
              if logger:
                logger.warning(f"[SETTINGS] select_agenda_by_user_id not ok: {agenda_result}")
          except Exception as e:
            if logger:
              logger.exception(f"[SETTINGS] Error calling select_agenda_by_user_id: {e}")
            st.warning(f"Could not load agenda from backend; using defaults. {e}")
        else:
          if logger:
            logger.info("[SETTINGS] Missing user_id; using defaults")
          st.write("⚠️ No user_id in session_state; skipping agenda fetch")

        # --------------------------
        # Set cookies (no tokens, no expiry cookie)
        # --------------------------

        # Mark logged in and switch page
        st.write("🔓 Marking session_state['is_login'] = True")
        st.session_state["is_login"] = True

        st.write("🧭 Calling PageSetter.set_dashboard()")
        PageSetter.set_dashboard()

        st.write("🔁 Calling st.rerun() (execution will restart here)")
        st.rerun()

      else:
        st.write("❌ sign_in returned error")
        st.error(result.get("error", "Login failed."))

  st.divider()

  st.caption("Forgot your password?")
  if st.button("🔁 Reset password"):
    st.write("🔁 Reset password button clicked; switching panel to 'forgot'")
    st.session_state["auth_panel"] = "forgot"

  st.caption("New here?")
  if st.button("📝 Create account"):
    st.write("📝 Create account button clicked; switching panel to 'sign_up'")
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
      result = sign_up(supabase, logger, email, password)

      if result.get("ok"):
        # --- New block: mirror login's auth/session handling ---
        st.write("✅ sign_up returned ok")

        auth_resp = result.get("data")
        st.write("📦 auth_resp present:", auth_resp is not None)

        if auth_resp is None:
          st.error("Sign up succeeded but no auth data.")
          return

        session_obj = getattr(auth_resp, "session", None)
        user_obj = getattr(auth_resp, "user", None)

        st.write("📦 session_obj present:", session_obj is not None)
        st.write("📦 user_obj present:", user_obj is not None)

        if session_obj is None:
          st.error("Sign up succeeded but missing session.")
          return

        # Store session info in session_state only (no tokens in cookies)
        st.session_state["auth_token"] = getattr(session_obj, "access_token", None)
        st.session_state["refresh_token"] = getattr(session_obj, "refresh_token", None)
        st.session_state["session_expires_at"] = getattr(session_obj, "expires_at", None)

        st.write("🔑 auth_token exists:", bool(st.session_state["auth_token"]))
        st.write("🔄 refresh_token exists:", bool(st.session_state["refresh_token"]))
        st.write("⏳ session_expires_at:", st.session_state["session_expires_at"])

        # Store user info
        if user_obj is not None:
          st.session_state["user_id"] = getattr(user_obj, "id", None)
          st.session_state["user_email"] = getattr(user_obj, "email", email)
        else:
          st.session_state["user_id"] = None
          st.session_state["user_email"] = email

        st.write("👤 user_id:", st.session_state["user_id"])
        st.write("👤 user_email:", st.session_state["user_email"])

        # Mark is_onboarding
        st.write("🔓 Marking session_state['is_onboarding'] = True")
        st.session_state["is_onboarding"] = True

        # Then go to onboarding
        st.write("🧭 Calling PageSetter.set_onboarding()")
        PageSetter.set_onboarding()
        st.rerun()

      else:
        st.error(result.get("error", "Sign up failed."))

  if st.button("⬅ Back to login"):
    st.session_state["auth_panel"] = "login"

# --------------------------
# FORGOT PASSWORD
# --------------------------
def render_forgot_password():
  st.header("🔁 Reset password")
  st.write("Enter your email and we’ll send a reset link to your inbox.")

  supabase = st.session_state.get("db_client")
  logger = st.session_state.get("logger")

  if not supabase:
    st.error("Supabase client missing: session_state['db_client'] not set.")
    return

  with st.form("forgot_form"):
    email = st.text_input("Email", key="forgot_email")
    submitted = st.form_submit_button("Send reset link")

    if submitted:
      if not email:
        st.error("Please enter your email address.")
        return

      # --- call the SYNC API function ---
      result = reset_password_for_email(
        supabase=supabase,
        logger=logger,
        email=email,
        redirect_to=None    # 👈 keep redirect None exactly as requested
      )

      if result.get("ok"):
        st.success(f"Reset link sent to **{email}**.")
      else:
        st.error(result.get("error", "Failed to send reset email."))

def render_onboarding():
  st.header("🎉 Welcome! Let's set up your first agenda.")

  st.write("🧪 render_onboarding() started")

  user_id = st.session_state.get("user_id")
  logger = st.session_state.get("logger")

  st.write("👤 user_id detected:", user_id)
  st.write("📝 logger exists:", bool(logger))

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

    st.write("📌 select Type")
    type_choice = st.selectbox("Type", TYPE_OPTIONS)

    st.write("📌 select Location")
    location_choice = st.selectbox("Location", LOCATION_OPTIONS)

    submitted = st.form_submit_button("Create agenda")

  # -------------------------
  # ON SUBMIT
  # -------------------------
  if submitted:
    st.write("📨 Onboarding form submitted")
    st.write("➡️ user_name:", user_name)
    st.write("➡️ agenda_name:", agenda_name)
    st.write("➡️ subreddit:", subreddit)
    st.write("➡️ type:", type_choice)
    st.write("➡️ location:", location_choice)

    if not user_name or not agenda_name or not subreddit:
      st.error("All fields are required.")
      return

    payload_data = {
      "type": type_choice,
      "location": location_choice
    }

    st.write("📦 Sending payload to create_agenda():")
    st.json({
      "subreddit": subreddit,
      "user_id": user_id,
      "name": agenda_name,
      "user_name": user_name,
      "data": payload_data
    })

    result = create_agenda(
      logger=logger,
      subreddit=subreddit,
      user_id=user_id,
      name=agenda_name,
      user_name=user_name,
      data=payload_data
    )

    st.write("📬 create_agenda() result:")
    st.write(result)

    if not result.get("ok"):
      st.error(result.get("error", "Failed to create agenda."))
      return

    # -------------------------
    # SAVE DATA TO SESSION STATE
    # -------------------------
    row = result.get("data") or {}

    st.write("🧩 Saving returned agenda data:", row)

    st.session_state["agenda_id"] = row.get("id")
    st.session_state["agenda_name"] = row.get("name")
    st.session_state["agenda_subreddit"] = row.get("subreddit")
    st.session_state["agenda_type"] = row.get("data", {}).get("type")
    st.session_state["agenda_location"] = row.get("data", {}).get("location")
    st.session_state["user_name"] = row.get("user_name")

    st.write("🔐 Marking session_state['is_login'] = True")
    st.session_state["is_login"] = True

    st.success("🎉 Agenda created! Redirecting to dashboard...")

    st.write("🧭 Calling PageSetter.set_dashboard()")
    PageSetter.set_dashboard()

    st.rerun()
