import streamlit as st
from modules.mock import MOCK_PROFILE, MOCK_AGENDA, TYPE_OPTIONS, LOCATION_OPTIONS

def render_settings():
  st.header("⚙️ Settings")

  # --- Profile section ---
  st.subheader("👤 Profile")
  with st.form("profile_form"):
    name = st.text_input("Name", value=MOCK_PROFILE.get("name", ""))
    email = st.text_input("Email", value=MOCK_PROFILE.get("email", ""))
    submitted = st.form_submit_button("Save profile")

    if submitted:
      MOCK_PROFILE["name"] = name
      MOCK_PROFILE["email"] = email
      st.success("Profile saved (mock).")

  st.divider()

  # --- Agenda section ---
  st.subheader("🗓️ Agenda")
  with st.form("agenda_form"):
    agenda_name = st.text_input("Agenda name", value=MOCK_AGENDA["agenda_name"])
    subreddit = st.text_input("Subreddit", value=MOCK_AGENDA["subreddit"])
    data_type = st.selectbox("Type", TYPE_OPTIONS, index=TYPE_OPTIONS.index(MOCK_AGENDA["data"]["type"]))
    location = st.selectbox("Location", LOCATION_OPTIONS, index=LOCATION_OPTIONS.index(MOCK_AGENDA["data"]["location"]))
    submitted = st.form_submit_button("Save changes")

    if submitted:
      MOCK_AGENDA["agenda_name"] = agenda_name
      MOCK_AGENDA["subreddit"] = subreddit
      MOCK_AGENDA["data"] = {"type": data_type, "location": location}
      st.success("Agenda updated (mock).")

  st.divider()

  # --- Password reset section ---
  st.subheader("🔑 Password")
  with st.form("reset_form"):
    email = st.text_input("Email", value=MOCK_PROFILE["email"], disabled=True)
    submitted = st.form_submit_button("Send reset link")

    if submitted:
      st.info(f"Mock: reset link sent to **{email}**.")

  st.divider()

  # --- Delete account section ---
  st.subheader("🗑️ Delete account")
  open_delete = st.checkbox("Show delete confirmation")
  if open_delete:
    with st.form("delete_form"):
      confirm = st.text_input("Type DELETE to confirm")
      submitted = st.form_submit_button("Confirm delete", disabled=confirm != "DELETE")

      if submitted:
        st.error("Account deleted (mock).")
