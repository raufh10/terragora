import streamlit as st
from modules.mock import MOCK_USERS

def render_login():
  st.header("🔐 Log in")

  with st.form("login_form"):
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    submitted = st.form_submit_button("Sign in")

    if submitted:
      if email in MOCK_USERS and MOCK_USERS[email] == password:
        st.success(f"Welcome back, **{email}**!")
      else:
        st.error("Invalid email or password.")

  st.divider()
  st.caption("Forgot your password?")
  if st.button("🔁 Reset password (mock)"):
    st.info("This would open the forgot-password form.")

  st.caption("New here?")
  if st.button("📝 Create account (mock)"):
    st.info("This would open the sign-up form.")

def render_sign_up():
  st.header("📝 Create account")

  with st.form("signup_form"):
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
    submitted = st.form_submit_button("Create account")

    if submitted:
      if password != confirm:
        st.error("Passwords do not match.")
      elif not email:
        st.warning("Please enter your email.")
      else:
        MOCK_USERS[email] = password
        st.success(f"Account created for **{email}** (mock).")

def render_forgot_password():
  st.header("🔁 Reset password")
  st.write("Enter your email and we’ll send a reset link (mock).")

  with st.form("forgot_form"):
    email = st.text_input("Email", key="forgot_email")
    submitted = st.form_submit_button("Send reset link")

    if submitted:
      if email in MOCK_USERS:
        st.info(f"Mock: password reset link sent to **{email}**.")
      else:
        st.error("Email not found.")
