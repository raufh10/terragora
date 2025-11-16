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

  st.write("🧪 render_login() started")

  cookie_ctrl = CookieController()
  st.write("🍪 CookieController initialized")

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

        # Store session info in session_state only (no cookies)
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

        # --------------------------
        # Set cookies (no tokens, no expiry cookie)
        # --------------------------
        st.write("🍪 Preparing to set cookies (user_id, user_email, has_session only)...")
        expires_at = st.session_state.get("session_expires_at")

        # simple expiration calculation, still used for user_id/email/has_session
        max_age = None
        if isinstance(expires_at, (int, float)):
          delta = int(expires_at - time.time())
          st.write("⏳ Raw delta until expiry (seconds):", delta)
          if delta > 0:
            max_age = delta

        st.write("⏳ max_age to use for cookies:", max_age)

        user_id = st.session_state.get("user_id")
        user_email = st.session_state.get("user_email")

        st.write("📦 Cookie payloads → user_id:", user_id)
        st.write("📦 Cookie payloads → user_email:", user_email)

        # Basic user cookies
        if user_id:
          st.write("🍪 Setting cookie user_id")
          cookie_ctrl.set("user_id", user_id, path="/", max_age=max_age, same_site="lax", secure=False)
        else:
          st.write("⚠️ user_id missing, not setting user_id cookie")

        if user_email:
          st.write("🍪 Setting cookie user_email")
          cookie_ctrl.set("user_email", user_email, path="/", max_age=max_age, same_site="lax", secure=False)
        else:
          st.write("⚠️ user_email missing, not setting user_email cookie")

        # Simple login marker
        st.write("🍪 Setting cookie has_session=1")
        cookie_ctrl.set("has_session", "1", path="/", max_age=max_age, same_site="lax", secure=False)

        # ⚠️ Removed: access_token / refresh_token / session_expires_at cookies
        st.write("❌ Skipping token + expiry cookies (Chrome-token issue workaround)")

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
