import streamlit as st
from modules.api import select_agenda_by_user_id

TYPE_OPTIONS = ["real_estate_agent", "electrician", "mechanic"]
LOCATION_OPTIONS = ["global", "US"]

def render_settings():
  st.header("⚙️ Settings")

  logger = st.session_state.get("logger")
  user_id = st.session_state.get("user_id")
  user_email = st.session_state.get("user_email", "")

  # ---- Defaults ----
  name_val = ""
  agenda_name_val = ""
  subreddit_val = ""
  data_type_val = TYPE_OPTIONS[0] if TYPE_OPTIONS else ""
  location_val = LOCATION_OPTIONS[0] if LOCATION_OPTIONS else ""

  # ---- Fetch agenda/profile from backend ----
  if user_id:
    try:
      result = select_agenda_by_user_id(logger, user_id)
      st.write(result)
      if result.get("ok") and result.get("data"):
        row = result["data"]
        name_val = row.get("user_name", "") or ""
        agenda_name_val = row.get("name", "") or ""
        subreddit_val = row.get("subreddit", "") or ""
        data_type_val = row.get("data_type", data_type_val) or data_type_val
        location_val = row.get("location", location_val) or location_val
        if logger:
          logger.info(f"[SETTINGS] Loaded agenda for user_id={user_id}")
      else:
        if logger:
          logger.warning(f"[SETTINGS] select_agenda_by_user_id not ok: {result}")
    except Exception as e:
      if logger:
        logger.exception(f"[SETTINGS] Error calling select_agenda_by_user_id: {e}")
      st.warning(f"Could not load agenda from backend; using defaults. {e}")
  else:
    if logger:
      logger.info("[SETTINGS] Missing user_id; using defaults")

  # ==========================
  # 1) PROFILE
  # ==========================
  st.subheader("👤 Profile")
  with st.form("profile_form"):
    name = st.text_input("Name", value=name_val)
    email = st.text_input("Email", value=user_email)
    submitted = st.form_submit_button("Save profile")

    if submitted:
      # For now, just acknowledge; wiring to backend can come later
      st.success("Profile saved (not yet wired to backend).")

  st.divider()

  # ==========================
  # 2) AGENDA
  # ==========================
  st.subheader("🗓️ Agenda")
  with st.form("agenda_form"):
    agenda_name = st.text_input("Agenda name", value=agenda_name_val)
    subreddit = st.text_input("Subreddit", value=subreddit_val)

    # Guard against missing/invalid values
    if data_type_val in TYPE_OPTIONS:
      type_index = TYPE_OPTIONS.index(data_type_val)
    else:
      type_index = 0

    if location_val in LOCATION_OPTIONS:
      location_index = LOCATION_OPTIONS.index(location_val)
    else:
      location_index = 0

    data_type = st.selectbox("Type", TYPE_OPTIONS, index=type_index)
    location = st.selectbox("Location", LOCATION_OPTIONS, index=location_index)

    submitted = st.form_submit_button("Save changes")

    if submitted:
      # Again, just mock feedback for now
      st.success("Agenda updated (not yet wired to backend).")

  st.divider()

  # ==========================
  # 3) PASSWORD RESET
  # ==========================
  st.subheader("🔑 Password")
  with st.form("reset_form"):
    email_display = user_email
    email = st.text_input("Email", value=email_display, disabled=True)
    submitted = st.form_submit_button("Send reset link")

    if submitted:
      st.info(f"Reset link request sent for **{email}** (hook up to supabase reset API).")

  st.divider()

  # ==========================
  # 4) DELETE ACCOUNT
  # ==========================
  st.subheader("🗑️ Delete account")
  open_delete = st.checkbox("Show delete confirmation")
  if open_delete:
    with st.form("delete_form"):
      confirm = st.text_input("Type DELETE to confirm")
      submitted = st.form_submit_button("Confirm delete", disabled=confirm != "DELETE")

      if submitted:
        st.error("Account deleted (mock; wire to backend delete endpoint).")
