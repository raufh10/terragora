import streamlit as st
from modules.config import get_email_regex, get_preferences
from modules.document import extract_text
from modules.api import (
  scan_streamlit_uploaded_file,
  create_token
)

def render_resume_tab(logger):

  try:
    with st.form("resume_form"):

      # --- Token Generation ---
      try:
        token = create_token(logger)
        st.session_state["token"] = token
        logger.info("🔐 Ephemeral token obtained for form session")
        logger.debug(f"Token present={bool(token)}")

      except Exception as e:
        logger.exception(f"❌ Failed to create token: {e}")

      # --- Title ---
      st.markdown("<h3 style='text-align: center;'>🎯 Data Analyst Jobs Matchmaker</h3>", unsafe_allow_html=True)
      st.markdown("<p style='text-align: center; color: gray;'>Upload your resume once and receive a clear compatibility analysis for new job listings.</p>", unsafe_allow_html=True)

      # --- Upload Page Initialization ---
      file_dict = {}
      text_dict = {}
      upload_tab, text_tab = st.tabs(["📄 Upload your resume", "✍️ Paste your resume"])

      # --- Upload Tab ---
      with upload_tab:
        uploaded_resume = st.file_uploader(
          "Upload a PDF or DOCX file",
          type=["pdf", "docx"],
        )

        if uploaded_resume:
          try:
            logger.info(f"📄 File uploaded: name={getattr(uploaded_resume, 'name', 'unknown')} type={getattr(uploaded_resume, 'type', 'unknown')}")

            # -- Scan Resume for Virus --
            scan_result = scan_streamlit_uploaded_file(logger, uploaded_resume)
            logger.debug(f"Scan result: {scan_result}")

            if scan_result is None:
              logger.warning("Resume scan could not be completed. Prompting user to try again.")
              st.error("We were unable to scan your file. Please try again with a different document.")
              return

            if scan_result.get("infected"):
              logger.warning("Infected file detected during upload. Alerting user.")
              st.error("⚠️ Unfortunately, this file appears to contain a security risk and cannot be processed.")
              return

            # -- Extract Resume File(PDF or DOCX) --
            try:
              try:
                uploaded_resume.seek(0)
              except Exception:
                logger.debug("uploaded_resume.seek(0) not supported; continuing")

              resume_bytes = uploaded_resume.read()
              if not resume_bytes:
                logger.warning("Uploaded file appears empty on read()")
                st.error("We couldn’t read this file. Please upload another PDF or DOCX to continue.")
                return

              resume_text = extract_text(
                uploaded_resume.type,
                resume_bytes,
                logger
              )
            except Exception as e:
              logger.exception(f"❌ Exception occurred while extracting text from uploaded resume: {e}")
              st.error("We couldn’t read this file. Please upload another PDF or DOCX to continue.")
              return

            # -- Generate Resume Dictionary --
            if not resume_text or not str(resume_text).strip():
              logger.warning("Extracted resume text is empty after parsing")
              st.error("We couldn’t extract text from this file. Please try another PDF or DOCX.")
              return

            file_dict = {
              "file": {
                "data": {"text": str(resume_text).strip()}
              }
            }
            logger.info("✅ Resume uploaded, scanned, and processed successfully.")
            st.success("✅ Your resume has been uploaded, scanned, and processed successfully.")

          except Exception as e:
            logger.exception(f"Resume parsing failed due to an unexpected error: {e}")
            st.error("We couldn’t read this file. Please upload another PDF or DOCX to continue.")

      # --- Text Tab ---
      with text_tab:
        try:
          resume_text = st.text_area(
            "Paste your resume text",
            height=400,
            max_chars=8000,
            key="resume_text_input",
            placeholder="Paste your resume here…"
          )

          # -- Generate Resume Dictionary --
          if resume_text:
            safe_text = resume_text.strip()
            
            if safe_text:
              text_dict = {
                "text": {
                  "data": {"text": safe_text}
                }
              }
            
              logger.info("📝 Resume text provided successfully.")
              logger.debug(f"Text resume length={len(safe_text)}")
              st.success("✅ Your resume has been parsed successfully.")
            
            else:
              logger.debug("User entered only whitespace in resume text area")

        except Exception as e:
          logger.exception(f"❌ Exception while handling text resume input: {e}")

      # --- Email Section ---
      try:
        email = st.text_input("Email Address", placeholder="you@example.com")

      except Exception as e:
        logger.exception(f"❌ Exception while rendering email input: {e}")
        email = ""

      # --- Name Section ---
      try:
        st.caption("Your name is needed to facilitate **anonymization of your resume**.")
        nc1, nc2 = st.columns(2)

        with nc1:
          first_name = st.text_input("First Name (optional)", placeholder="john")
        with nc2:
          last_name = st.text_input("Last Name (optional)", placeholder="doe")

      except Exception as e:
        logger.exception(f"❌ Exception while rendering email input: {e}")
        first_name = ""
        last_name = ""

      # --- Submit Button ---
      sc1, sc2, sc3 = st.columns(3)

      with sc2:
        submitted = st.form_submit_button(
          "Continue",
          type="primary",
          width="stretch"
        )

        if submitted:
          try:

            # -- Generate Combined Resume Dictionary --
            st.session_state["resume"] = (file_dict or {}) | (text_dict or {})
            logger.debug(f"Submission clicked | has_file_dict={bool(file_dict)} has_text_dict={bool(text_dict)}")

            # -- Email Regex Check --
            try:
              email_regex = get_email_regex()
            except Exception as e:
              logger.exception(f"❌ Failed to get email regex from config: {e}")
              email_regex = None

            # -- Dictionaries Validations --
            if not email or not email.strip():
              logger.warning("User attempted to save profile with an empty email address.")
              st.error("Please provide a valid email address before continuing.")

            elif email_regex and not email_regex.match(email.strip()):
              logger.warning("User attempted to save profile with an invalid email address.")
              st.error("Please provide a valid email address before continuing.")

            elif not st.session_state.get("resume"):
              logger.warning("User attempted to save profile without providing resume text.")
              st.error("Please provide your resume text before continuing.")

            # -- Generate User Profile Dictionary --
            else:
              st.session_state["user_profile"] = {
                "name": {
                  "first_name": first_name,
                  "last_name": last_name
                },
                "email": email.strip(),
                "preferences": get_preferences()
              }
              logger.info(f"✅ Profile saved successfully for email={email.strip()}")
  
          except Exception as e:
            logger.exception(f"❌ Exception during form submission: {e}")

  except Exception as e:
    logger.exception(f"💥 Unexpected error in render_resume_tab: {e}")
    st.error("An unexpected error occurred while rendering this section.")
