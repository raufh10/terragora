import streamlit as st
from modules.api import setup_profile
from modules.utils.data import get_resume_text

def render_confirmation(logger):
  try:
    logger.info("📝 Rendering confirmation step")

    st.markdown("<h3 style='text-align: center;'>📄 Review and Confirm Your Submission</h3>", unsafe_allow_html=True)
    user_profile = st.session_state.get("user_profile", {})
    first_name = user_profile.get('name', {}).get('first_name', '')
    last_name = user_profile.get('name', {}).get('last_name', '')

    resume, resume_text = get_resume_text(
      st.session_state.get("resume", {}),
      logger
    )
    logger.debug(f"Resume present={bool(resume)} | User profile keys={list(user_profile.keys()) if isinstance(user_profile, dict) else 'N/A'}")

    if not resume or not user_profile:
      logger.warning("⚠️ Missing resume or user profile before confirmation")
      st.warning("⚠️ Please upload/paste your resume and fill in your profile first.")
      return

    with st.container(border=True):
      st.write(f"**Email:** {user_profile.get('email', '-')}")

      st.write(f"**Name:** {first_name} {last_name}".strip() or "-")
      if not first_name or not last_name:
        st.warning("⚠️ Your name is missing or incomplete, without it, our **anonymization process** may be incomplete. Please check your entries.")

      st.write(f"**Resume:**")
      st.text(resume_text)

      sc1, sc2, sc3 = st.columns(3)
      with sc2:
        if st.button("Submit", type="primary", width="stretch"):
          logger.info("Confirm and Submit button clicked")

          try:
            st.session_state["confirmation"] = {
              "resume": resume,
              "user_profile": user_profile,
              "token": st.session_state.get("token", "")
            }
            logger.debug(f"Confirmation state built for email={user_profile.get('email')}")

            if setup_profile(logger, st.session_state["confirmation"]):
              logger.info("✅ Profile setup completed successfully")
              st.session_state["submit"] = True
            else:
              logger.warning("⚠️ setup_profile returned None or not-ok result")
              st.session_state["submit"] = False

          except Exception as e:
            logger.exception(f"💥 Exception while submitting profile: {e}")
            st.error("An unexpected error occurred while submitting your profile. Please try again.")

  except Exception as e:
    logger.exception(f"💥 Unexpected error in render_confirmation: {e}")
    st.error("An error occurred while rendering the confirmation step.")
