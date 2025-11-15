import time
import streamlit as st
from streamlit_cookies_controller import CookieController
from modules.api import sign_in, sign_up, reset_password_for_email
from modules.setter import PageSetter

# --------------------------
# LOGIN
# --------------------------
def render_login():
  st.header("🔐 Log in")

  cookie_ctrl = CookieController()

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
      result = sign_in(supabase, logger, email, password)

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

        # Store session info
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

        # --------------------------
        # Set cookies (dev mode)
        # --------------------------
        expires_at = st.session_state.get("session_expires_at")

        # simple expiration calculation
        max_age = None
        if isinstance(expires_at, (int, float)):
          delta = int(expires_at - time.time())
          if delta > 0:
            max_age = delta

        user_id = st.session_state.get("user_id")
        user_email = st.session_state.get("user_email")
        auth_token = st.session_state.get("auth_token")
        refresh_token = st.session_state.get("refresh_token")

        # Basic user cookies
        if user_id:
          cookie_ctrl.set("user_id", user_id, path="/", max_age=max_age, same_site="lax", secure=False)
        if user_email:
          cookie_ctrl.set("user_email", user_email, path="/", max_age=max_age, same_site="lax", secure=False)

        # Simple login marker
        cookie_ctrl.set("has_session", "1", path="/", max_age=max_age, same_site="lax", secure=False)

        # Dev-only tokens in cookies
        if auth_token:
          cookie_ctrl.set("access_token", auth_token, path="/", max_age=max_age, same_site="lax", secure=False)
        if refresh_token:
          cookie_ctrl.set("refresh_token", refresh_token, path="/", max_age=max_age, same_site="lax", secure=False)

        if expires_at:
          cookie_ctrl.set("session_expires_at", str(expires_at), path="/", max_age=max_age, same_site="lax", secure=False)

        # Mark logged in and switch page
        st.session_state["is_login"] = True
        PageSetter.set_dashboard()
        st.rerun()

      else:
        st.error(result.get("error", "Login failed."))

  st.divider()

  st.caption("Forgot your password?")
  if st.button("🔁 Reset password"):
    st.session_state["auth_panel"] = "forgot"

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
      result = sign_up(supabase, logger, email, password)

      if result.get("ok"):
        st.success(f"Account created for **{email}**!")
        st.session_state["auth_panel"] = "login"
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
