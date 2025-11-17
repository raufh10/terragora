import streamlit as st
from modules.api import (
  select_agenda_by_user_id,
  edit_agenda,
  set_session_from_tokens,
  update_user_email,
)
from modules.config import TYPE_OPTIONS, LOCATION_OPTIONS

def render_settings():
  st.header("⚙️ Settings")

  logger = st.session_state.get("logger")
  user_id = st.session_state.get("user_id")
  user_email = st.session_state.get("user_email", "")

  # ---- Defaults pulled from session_state ----
  name_val = st.session_state.get("user_name")
  agenda_name_val = st.session_state.get("agenda_name")
  subreddit_val = st.session_state.get("agenda_subreddit")
  data_type_val = st.session_state.get("agenda_type")
  location_val = st.session_state.get("agenda_location")
  agenda_id_val = st.session_state.get("agenda_id")

  # ==========================
  # 1) PROFILE
  # ==========================
  st.subheader("👤 Profile")
  with st.form("profile_form"):
    name = st.text_input("Name", value=name_val)
    email = st.text_input("Email", value=user_email)
    submitted = st.form_submit_button("Save profile")

    if submitted:
      # Always update local name in session_state
      st.session_state["user_name"] = name

      # Only attempt Supabase email update if the email actually changed
      if email != user_email:
        supabase = st.session_state.get("db_client")
        access_token = st.session_state.get("auth_token")
        refresh_token = st.session_state.get("refresh_token")

        if not supabase or not access_token or not refresh_token:
          st.error("Missing Supabase client or auth tokens; cannot update email.")
          if logger:
            logger.warning(
              "[SETTINGS] Email change requested but db_client/auth tokens missing"
            )
        else:
          # 1) Restore Supabase auth session from tokens
          if logger:
            logger.info("[SETTINGS] Calling set_session_from_tokens before email update")

          sess_result = set_session_from_tokens(
            supabase=supabase,
            logger=logger,
            access_token=access_token,
            refresh_token=refresh_token,
          )

          if not sess_result.get("ok"):
            st.error(sess_result.get("error", "Failed to restore session before updating email."))
          else:
            # 2) Actually update email in Supabase
            if logger:
              logger.info(f"[SETTINGS] Calling update_user_email with new_email={email!r}")

            upd_result = update_user_email(
              supabase=supabase,
              logger=logger,
              new_email=email,
            )

            if upd_result.get("ok"):
              st.session_state["user_email"] = email
              st.success("Profile and email updated.")
            else:
              st.error(upd_result.get("error", "Failed to update email."))
      else:
        # Name changed but email stayed the same
        st.success("Profile updated.")

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
      if not agenda_id_val:
        st.error("No agenda loaded from backend; cannot update agenda (missing agenda_id).")
        if logger:
          logger.warning("[SETTINGS] Save agenda clicked but agenda_id is missing")
      else:
        payload_data = {
          "type": data_type,
          "location": location,
        }
        if logger:
          logger.info(
            f"[SETTINGS] Submitting edit_agenda for agenda_id={agenda_id_val} "
            f"name={agenda_name!r} subreddit={subreddit!r} data={payload_data!r}"
          )

        result = edit_agenda(
          logger=logger,
          agenda_id=agenda_id_val,
          name=agenda_name,
          subreddit=subreddit,
          data=payload_data,
        )

        if result.get("ok"):
          st.success("Agenda updated.")
        else:
          st.error(result.get("error", "Failed to update agenda."))

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
