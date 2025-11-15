import streamlit as st
from modules.api import sign_in, sign_up, reset_password_for_email

# --------------------------
# LOGIN
# --------------------------
def render_login():
  st.header("🔐 Log in")

  supabase = st.session_state.get("db_client")
  if not supabase:
    st.error("Supabase client missing: session_state['db_client'] not set.")
    return

  with st.form("login_form"):
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    submitted = st.form_submit_button("Sign in")

    if submitted:
      logger = st.session_state.get("logger")
      result = sign_in(supabase, logger, email, password)

      if result.get("ok"):
        # depending on how _ok() is structured in modules.api
        session = result.get("data", {}) or result.get("session", {})
        st.session_state["auth_token"] = session.get("access_token")
        st.success(f"Welcome back, **{email}**!")
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
