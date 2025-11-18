import streamlit as st
from modules.api import (
  select_agenda_by_user_id,
  edit_agenda,
  set_session_from_tokens,
  update_user_email,
  admin_delete_user,
  admin_update_user_email,
  admin_update_user_password
)
from modules.config import TYPE_OPTIONS, LOCATION_OPTIONS


def render_profile():
  logger = st.session_state.get("logger")
  user_id = st.session_state.get("user_id")
  user_email = st.session_state.get("user_email", "")
  name_val = st.session_state.get("user_name")

  st.subheader("👤 Profile")

  with st.form("profile_form"):
    name = st.text_input("Name", value=name_val)
    email = st.text_input("Email", value=user_email)
    submitted = st.form_submit_button("Save profile")

    if submitted:
      # Always update local name
      st.session_state["user_name"] = name

      # Only try to update email if changed
      if email != user_email:
        if not user_id:
          st.error("Missing user_id; cannot update email.")
          if logger:
            logger.warning("[SETTINGS] Email change requested but user_id missing")
        else:
          if logger:
            logger.info(
              f"[SETTINGS] Calling admin_update_user_email for user_id={user_id} "
              f"new_email={email!r}"
            )

          result = admin_update_user_email(
            logger=logger,
            user_id=user_id,
            new_email=email,
          )

          if result.get("ok"):
            st.session_state["user_email"] = email
            st.success("Profile and email updated.")
          else:
            st.error(result.get("error", "Failed to update email."))
      else:
        st.success("Profile updated.")


def render_agenda():
  logger = st.session_state.get("logger")
  agenda_name_val = st.session_state.get("agenda_name")
  subreddit_val = st.session_state.get("agenda_subreddit")
  data_type_val = st.session_state.get("agenda_type")
  location_val = st.session_state.get("agenda_location")
  agenda_id_val = st.session_state.get("agenda_id")

  st.subheader("🗓️ Agenda")

  with st.form("agenda_form"):
    agenda_name = st.text_input("Agenda name", value=agenda_name_val)
    subreddit = st.text_input("Subreddit", value=subreddit_val)

    # Safe defaults
    type_index = TYPE_OPTIONS.index(data_type_val) if data_type_val in TYPE_OPTIONS else 0
    location_index = (
      LOCATION_OPTIONS.index(location_val) if location_val in LOCATION_OPTIONS else 0
    )

    data_type = st.selectbox("Type", TYPE_OPTIONS, index=type_index)
    location = st.selectbox("Location", LOCATION_OPTIONS, index=location_index)

    submitted = st.form_submit_button("Save changes")

    if submitted:
      if not agenda_id_val:
        st.error("No agenda loaded from backend; cannot update agenda.")
        if logger:
          logger.warning("[SETTINGS] Save agenda clicked but agenda_id missing")
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


def render_change_password():
  logger = st.session_state.get("logger")
  user_id = st.session_state.get("user_id")
  user_email = st.session_state.get("user_email", "")

  st.subheader("🔑 Password")

  with st.form("password_form"):
    confirm_email = st.text_input(
      "Type your account email to confirm",
      value="",
      placeholder="your@email.com",
    )
    new_password = st.text_input(
      "New password",
      type="password",
      placeholder="Enter a new password",
    )
    submitted = st.form_submit_button("Change password")

    if submitted:
      if not user_id:
        st.error("Cannot update password: missing user_id in session.")
      elif not confirm_email:
        st.error("Please type your email to confirm.")
      elif confirm_email.strip() != (user_email or "").strip():
        st.error("Entered email does not match your current account email.")
      elif not new_password:
        st.error("Please enter a new password.")
      else:
        if logger:
          logger.info("[SETTINGS] Calling admin_update_user_password")

        resp = admin_update_user_password(
          logger=logger,
          user_id=user_id,
          new_password=new_password,
        )

        if resp.get("ok"):
          st.success("Password updated successfully.")
        else:
          st.error(resp.get("error", "Failed to update password."))


def render_delete_account():
  logger = st.session_state.get("logger")
  user_id = st.session_state.get("user_id")

  st.subheader("🗑️ Delete account")

  open_delete = st.checkbox("Show delete confirmation")

  if open_delete:
    with st.form("delete_form"):
      confirm = st.text_input("Type DELETE to confirm")
      submitted = st.form_submit_button("Confirm delete")

      if submitted:
        if not user_id:
          st.error("Missing user_id — cannot delete account.")
          if logger:
            logger.error("[SETTINGS] Delete clicked but user_id missing")
        else:
          if logger:
            logger.info(f"[SETTINGS] Calling admin_delete_user for user_id={user_id}")

          resp = admin_delete_user(logger, user_id)

          if not resp.get("ok"):
            st.error(resp.get("error", "Failed to delete account."))
          else:
            st.success("Your account has been permanently deleted.")

            # Clear local session_state
            for key in [
              "auth_token", "refresh_token", "session_expires_at",
              "user_id", "user_email", "user_name",
              "agenda_id", "agenda_name", "agenda_subreddit",
              "agenda_type", "agenda_location",
              "is_login",
            ]:
              st.session_state.pop(key, None)

            st.info("Session cleared. Please refresh.")
            st.rerun()
